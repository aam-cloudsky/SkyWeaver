# src/skyweaver/core/logistics/depot.py

from typing import Any, Dict, Optional, Tuple, cast
import threading

from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.reserved_id_enum import ReservedIDs


from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.core.logistics.parcel import Parcel, EmptyParcel
from skyweaver.core.logistics.depot_messages import DepotGet, DepotSet, DepotUpdate


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


# ---------------------------------------------------------------------
# AirspaceState — explicit, reactive, and clean
# ---------------------------------------------------------------------
class Depot(metaclass=ThreadSingleton):
    """Centralized singleton data registry for the SkyWeaver simulation.
    Holds all spatial entities and notifies listeners when updated.
    """

    def __init__(self):

        self._storage: Dict[type, Parcel] = {}
        self._null_parcel = EmptyParcel()

        self.publisher_id = ReservedIDs.DEPOT.value
        self.message_hub: MessageHub = MessageHub()
        self._subscribe_to_topics()

    # ------------------------------------------------------------------
    # Parcel Management
    # ------------------------------------------------------------------

    def get_parcel(self, parcel_type: type[Parcel]) -> Parcel:
        return self._storage.get(parcel_type, self._null_parcel)

    def set_parcel(self, parcel: Parcel):
        if not isinstance(parcel, Parcel):
            raise TypeError("Only Parcel instances can be registered")

        self._storage[type(parcel)] = parcel

    def get_parcels(self, parcel_types: list[type[Parcel]]) -> Dict[type, Parcel]:
        pallet: Dict[type, Parcel] = {}
        for ptype in parcel_types:
            parcel = self.get_parcel(ptype)
            pallet[ptype] = parcel
        return pallet
            
    # ------------------------------------------------------------------
    # Events Management
    # ------------------------------------------------------------------


    def _on_get_request(self, message: BaseMessage, context: MessageContext):
        if not isinstance(message, DepotGet):
            return
        
        mes: DepotGet = cast(DepotGet, message)
        parcel_types = mes.types
        pallet = self.get_parcels(parcel_types)

        self.message_hub.publish(
            topic=TopicsEnum.DEPOT_GET,
            message=DepotUpdate(pallet=pallet),
            message_context=self._build_answer_context(context)
        )


    def _on_set_request(self, message: BaseMessage, context: MessageContext):
        if not isinstance(message, DepotSet):
            return
        
        mes: DepotSet = cast(DepotSet, message)
        pallet = mes.pallet

        for parcel in pallet.values():
            self.set_parcel(parcel)

        MessageHub().publish(
            topic=TopicsEnum.DEPOT_SET,
            message=DepotUpdate(pallet=pallet),
            message_context=self._build_answer_context(context, to_id=ReservedIDs.BROADCAST.value)
        )
        
    def _build_answer_context(self, request_context: MessageContext, to_id: Optional[int] = None) -> MessageContext:
        """Build a response MessageContext based on a request's context."""
        return MessageContext(
            from_id=self.publisher_id,
            to_id=to_id if to_id is not None else request_context.from_id,
            reply_to=request_context.trace_id
         )

    # ------------------------------------------------------------------
    # MessageHub Registration and Subscription
    # ------------------------------------------------------------------

    def _subscribe_to_topics(self):
        """Subscribe to relevant MessageHub topics."""

        self.message_hub.subscribe(
            topic=TopicsEnum.DEPOT_GET,
            publisher_id=self.publisher_id,
            subscriber=self._on_get_request
        )

        self.message_hub.subscribe(
            topic=TopicsEnum.DEPOT_SET,
            publisher_id=self.publisher_id,
            subscriber=self._on_set_request
        )
