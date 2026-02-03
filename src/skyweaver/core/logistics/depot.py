# src/skyweaver/core/logistics/depot.py


from typing import Any, Dict, Optional, Tuple, cast
import threading
from skyweaver.core.bus.protocol.validity_message import ValidityMessage
from skyweaver.core.logistics.validity.sentinel import ValidityTransition, Sentinel

from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.enums.reserved_id_enum import ReservedIDs

from skyweaver.core.bus.runtime.hub import TopicsEnum, MessageContext
from skyweaver.core.logistics.lifecycle import LifecycleState, LifecycleStateMessage
from skyweaver.core.bus.runtime.port import Port
from skyweaver.core.logistics.parcel import Parcel
from skyweaver.core.logistics.depot_messages import DepotGet, DepotRegistry, DepotSet, DepotUpdate



# ---------------------------------------------------------------------
# Thread-local singleton (same pattern you already had)
# ---------------------------------------------------------------------
class ThreadSingleton(type):
    _instances: Dict[Tuple[type, int], Any] = {}

    def __call__(cls, *args, **kwargs):
        tid = threading.get_ident()
        key = (cls, tid)
        if key not in cls._instances:
            cls._instances[key] = super(
                ThreadSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]


class Depot(metaclass=ThreadSingleton):
    # self declared reserved
    __bus_id__ = ReservedIDs.DEPOT.value

    def __init__(self):

        self.sentinel = Sentinel()
        self._setup_port_hub()
        self._setup_storage()
        self._notify(LifecycleState.ACTIVE)

    def _setup_port_hub(self):

        self._registry_port = Port(
            owner=self,
            topic=TopicsEnum.DEPOT_REGISTRY,
            on_arrive=self._on_registry_request,
            on_end_arrive=self._on_end_registry_request,
        )

        self._get_port = Port(
            owner=self,
            topic=TopicsEnum.DEPOT_GET,
            on_arrive=self._on_get_request,
            on_end_arrive=self._on_end_get_request,
        )

        self._set_port = Port(
            owner=self,
            topic=TopicsEnum.DEPOT_SET,
            on_arrive=self._on_set_request,
            on_end_arrive=self._on_end_set_request,
        )

        self._validity_port = Port(
            owner=self,
            topic=TopicsEnum.VALIDITY,
        )

        self._lifecycle_port = Port(
            owner=self,
            topic=TopicsEnum.LIFECYCLE
        )

    # ------------------------------------------------------------------
    # Lifecycle Management
    # ------------------------------------------------------------------

    def _notify(self, state: LifecycleState):
        if getattr(self, "_last_lifecycle_state", None) != state:

            self._lifecycle_port.send(LifecycleStateMessage(state=state))
            self._last_lifecycle_state = state

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _on_registry_request(self, message: BaseMessage, context: MessageContext):
        depot_registry = cast(DepotRegistry, message)
        self.sentinel.register(message=depot_registry, context=context)

        return depot_registry, context.from_id, context.trace_id

    def _on_end_registry_request(self, result: Any):
        depot_registry, to_id, trace_id = result
        self._registry_port.send(message=DepotRegistry(outpost_type=depot_registry.outpost_type, parcels_by_role=depot_registry.parcels_by_role, registered=True)
                                 , to_id=to_id, reply_to=trace_id)


     # ------------------------------------------------------------------


    def _on_get_request(self, message: BaseMessage, context: MessageContext):

        if not isinstance(message, DepotGet):
            return
        
        mes: DepotGet = cast(DepotGet, message)
        parcel_types = mes.types
        return (self.get_pallet(parcel_types), context.from_id, context.trace_id)


    def _on_end_get_request(self, result: Any):
        pallet, to_id, trace_id = result
        self._get_port.send(
            DepotUpdate(pallet=pallet),
            to_id=to_id,
            reply_to=trace_id
        )

    def _on_set_request(self, message: BaseMessage, context: MessageContext):
        if not isinstance(message, DepotSet):
            return
        
        validity_transition: ValidityTransition = self.sentinel.verify_validity(
            message=cast(DepotSet, message), context=context)
        
        # TODO: Can ONLY mutate if valid! dismiss otherwise
        
        mes: DepotSet = cast(DepotSet, message)
        pallet = mes.pallet

        confirmed_parcels: Dict[type, Parcel] = {}
        for parcel in pallet.values():
            change_status = self.set_parcel(parcel)
            if change_status:
                confirmed_parcels[type(parcel)] = parcel
        return confirmed_parcels, validity_transition, context.from_id
    
    def _on_end_set_request(self, result: Any):
        confirmed_parcels, validity_transition, validity_source_id = result
        if (
            validity_transition.became_valid
            or validity_transition.became_invalid
        ):
            self._validity_port.send(
                ValidityMessage(validity_transition=validity_transition,
                                validity_source_id=validity_source_id)
            )
        
        self._set_port.send(
            DepotUpdate(pallet=confirmed_parcels),
            to_id=ReservedIDs.BROADCAST.value
        )
        
            
    # ------------------------------------------------------------------
    # Parcel Management
    # ------------------------------------------------------------------

    def _setup_storage(self):
        self._storage: Dict[type, Parcel] = {}

    def get_pallet(self, parcel_types: list[type[Parcel]]) -> Dict[type, Parcel]:
        """
        Only return registered parcels.
        """
        pallet: Dict[type, Parcel] = {}
        for ptype in parcel_types:
            parcel = self.get_parcel(ptype)
            if parcel:
                pallet[ptype] = parcel
        return pallet

    def get_parcel(self, parcel_type: type[Parcel]) -> Optional[Parcel]:
        return self._storage.get(parcel_type)

    def set_parcel(self, parcel: Parcel) -> bool:
        if not isinstance(parcel, Parcel):
            raise TypeError("Only Parcel instances can be registered")

        self._storage[type(parcel)] = parcel
        return True

    
