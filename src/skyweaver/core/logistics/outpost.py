from collections import defaultdict
from typing import  Callable, ClassVar, Dict, Type, Any, Optional, cast, get_origin, get_args
from dataclasses import dataclass, fields
from dataclasses import dataclass, field, fields
from typing import Dict, Optional, Set, Type

from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.logistics.depot_messages import DepotGet, DepotRegistry, DepotSet, DepotUpdate
from skyweaver.core.logistics.lifecycle import LifecycleState, LifecycleStateMessage
from skyweaver.core.bus.runtime.port import Port
from skyweaver.core.logistics.parcel import Parcel, ParcelRole



from enum import Enum, auto
from typing import get_origin, get_args


@dataclass(eq=False)
class OutpostParcelSchema:

    def parcel_definitions(self) -> Dict[Type[Parcel], Dict[str, Any]]:
        schema: Dict[Type[Parcel], Dict[str, Any]] = {}

        for f in fields(self):
            parcel_type = self._resolve_parcel_type(f)

            if not issubclass(parcel_type, Parcel):
                continue

            schema[parcel_type] = {
                "role": f.metadata.get("role", ParcelRole.UNDEFINED),
                "field": f.name,
            }

        return schema

    def _resolve_parcel_type(self, field) -> Type[Parcel]:
        annotation = field.type
        origin = get_origin(annotation)

        if origin is Optional:
            return get_args(annotation)[0]

        return annotation
    
    def _build_pallet(self):
        pallet: Dict[Type[Parcel], Parcel] = {}
        for parcel_type in self.parcel_definitions().keys():
            parcel = getattr(self, self.parcel_definitions()[parcel_type]["field"])
            if parcel is not None:
                pallet[parcel_type] = parcel
        return pallet
    
    @classmethod
    def parcels_by_role(
        cls
    ) -> Dict[ParcelRole, Set[Type[Parcel]]]:
        """
        Canonical projection of parcel roles declared in the Outpost schema.

        Returns a mapping:
            ParcelRole -> set[ParcelType]

        This method is intentionally generic: new ParcelRole values
        are automatically supported.
        """
        roles: Dict[ParcelRole, Set[Type[Parcel]]] = defaultdict(set)

        # usamos o schema declarativo da classe
        for f in fields(cls):
            parcel_type = cls._resolve_parcel_type_static(f)
            if not issubclass(parcel_type, Parcel):
                continue

            role = f.metadata.get("role", ParcelRole.UNDEFINED)
            roles[role].add(parcel_type)

        return dict(roles)

    @staticmethod
    def _resolve_parcel_type_static(field) -> Type[Parcel]:
        annotation = field.type
        origin = get_origin(annotation)

        if origin is Optional:
            return get_args(annotation)[0]

        return annotation

class OutpostOperationalStates(Enum):
    IDLE = auto()
    BEGINNING_OPERATION = auto()
    TRANSACTION = auto()
    ON_RECEIVING_FROM_DEPOT = auto()


@dataclass(frozen=True)
class StateFlags:
    _permit_external_parcels_mutation: bool
    _permit_internal_parcel_mutation: bool
    _permit_internal_private_mutation: bool


@dataclass(eq=False)
class Outpost(OutpostParcelSchema):
    """
    Reactive configuration unit synchronized via Depot.

    - Declares parcels as dataclass fields
    - CONSUMED parcels are dependencies
    - PRODUCED parcels are published after transactions

    # NOTE:
    # This system assumes strong synchronization.
    # Delivery failure indicates incorrect usage or initialization order.
    # Local state is not rolled back on failed delivery.

    """
    "Máquina Reativa Orientada a Eventos QUE ESCOLHE O ESTADO MAIS ADEQUADO A CADA EVENTO"
    

    _STATE_FLAG_MAP: ClassVar[Dict[OutpostOperationalStates, StateFlags]] = {
        OutpostOperationalStates.IDLE: StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=False,
            _permit_internal_private_mutation=False,
        ),
        OutpostOperationalStates.TRANSACTION: StateFlags(
            _permit_external_parcels_mutation=True,
            _permit_internal_parcel_mutation=True,
            _permit_internal_private_mutation=True,
        ),
        OutpostOperationalStates.BEGINNING_OPERATION: StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=True,
            _permit_internal_private_mutation=True,
        ),
        OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT: StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=True,
            _permit_internal_private_mutation=True,
        ),
    }


    #=======================================================
    # Operational State Management
    # =======================================================

    def __post_init__(self):
        
        self._init_flags()
        self._transition_state(OutpostOperationalStates.BEGINNING_OPERATION)
        self._setup_port_hub()
        
        self._request_pallet()


    def _init_flags(self):
        self._flags: StateFlags = StateFlags(_permit_external_parcels_mutation=False,
                                             _permit_internal_parcel_mutation=False,
                                             _permit_internal_private_mutation=True)

    def _notify(self, state: LifecycleState):
        if getattr(self, "_last_lifecycle_state", None) != state:
            
            self._lifecycle_port.send(LifecycleStateMessage(state=state))
            self._last_lifecycle_state = state

    def set_on_pallet_sync(self, callback: Callable[[Dict[Type[Parcel], Parcel]], None]):
        #self._on_pallet_sync: Callable[[Dict[Type[Parcel], Parcel]], None] = callback
        object.__setattr__(self, "_on_pallet_sync", callback)



    # =======================================================
    # Port Operations
    # =======================================================

    def _setup_port_hub(self):

        self._registry_port = Port(
            owner=self,
            topic=TopicsEnum.DEPOT_REGISTRY,
            on_arrive=self._on_registry_arrive,
            on_end_arrive=self._on_registry_arrive_end,
        )

        self._set_port = Port(
            owner=self,
            topic=TopicsEnum.DEPOT_SET,
            on_arrive=self._on_pallet_arrive,
            on_end_arrive=self._on_pallet_end,
        )

        self._get_port = Port(
            owner=self,
            topic=TopicsEnum.DEPOT_GET,
            on_arrive=self._on_get_pallet_arrive,
            on_end_arrive=self._on_get_pallet_end,
        )

        self._lifecycle_port = Port(
            owner=self,
            topic=TopicsEnum.LIFECYCLE
        )

        self._register_with_depot()

        

    def _register_with_depot(self):
        self._registry_port.send(
            DepotRegistry(
                outpost_type=type(self),
                parcels_by_role=self.parcels_by_role()
            )
        )

    def _on_registry_arrive(self, message: BaseMessage, context: MessageContext):
        depot_registry = cast(DepotRegistry, message)
        return depot_registry.registered

    def _on_registry_arrive_end(self, result: Any):
        registered = result
        if registered:
            self._notify(LifecycleState.JOINED)
        else:
            self._notify(LifecycleState.FAILED_TO_JOIN)

    def _on_get_pallet_arrive(self, message: BaseMessage, context: MessageContext):
        self._on_pallet_arrive(message, context)

    def _on_get_pallet_end(self, result):
        self._notify(LifecycleState.SYNCED)
        self._transition_state(OutpostOperationalStates.IDLE)

    #=======================================================
    # On Pallet Management
    #=======================================================

    def _request_pallet(self):
        pallet_types = list(self.parcel_definitions().keys())
        self._get_port.send(DepotGet(types=pallet_types))

    def _on_pallet_arrive(self, message: BaseMessage, context: MessageContext):

        mes = cast(DepotUpdate, message)
        self._transition_state(OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT)
        self._set_parcels(mes.pallet)
        
        _on_pallet_sync = getattr(self, "_on_pallet_sync", lambda pallet: None)
        _on_pallet_sync(self._build_pallet())

        
    def _on_pallet_end(self, _):
        self._transition_state(OutpostOperationalStates.IDLE)

    

    def _commit_pallet(self):
        pallet = self._build_pallet()
        if pallet:
            self._set_port.send(DepotSet(pallet=pallet))

    #=======================================================
    # Transaction Context
    #=======================================================    

    def __enter__(self):
        self._transition_state(OutpostOperationalStates.TRANSACTION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._commit_pallet()
        self._transition_state(OutpostOperationalStates.IDLE)
        

    def _transition_state(self, new_state: OutpostOperationalStates):
        """
        All state transitions must update flags accordingly.
        1. IDLE: no parcel changes allowed
        """
        #self._state = new_state
        #self._flags = self._STATE_FLAG_MAP[new_state]

        
        object.__setattr__(self, "_flags", self._STATE_FLAG_MAP[new_state])
        object.__setattr__(self, "_state", new_state)
        


    #======================================================
    # Flagged Functions
    # set parcels must only works within permitted contexts
    # it is blocked by __setattr__
    #=======================================================

    def _set_parcels(self, pallet: Dict[Type[Parcel], Parcel]):

        if not self._flags._permit_internal_parcel_mutation:
            raise RuntimeError(
                "_set_parcels called in a state that does not allow parcel mutation"
            )
    
        definitions = self.parcel_definitions()
        for parcel_type, parcel in pallet.items():
            if parcel_type not in definitions:
                continue   
            field_name = definitions[parcel_type]["field"]
            object.__setattr__(self, field_name, parcel)

    def __setattr__(self, name, value):
        
        # Durante __init__ / __post_init__, _flags ainda não existe
        if not hasattr(self, "_flags"):
            object.__setattr__(self, name, value)
            return

        if name.startswith("_") and self._flags._permit_internal_private_mutation:
            object.__setattr__(self, name, value)
            return
        
        if self._flags._permit_external_parcels_mutation:
            object.__setattr__(self, name, value)
            return
        
        raise AttributeError(
            "Direct assignment is disabled. "
            "Use 'with Outpost() as outpost:'"
        )