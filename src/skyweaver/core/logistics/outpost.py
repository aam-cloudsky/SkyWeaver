from typing import Callable, Dict, Type, Any, Optional, cast, get_origin, get_args
from dataclasses import dataclass, fields
from dataclasses import dataclass, field, fields
from typing import Dict, List, Optional, Set, Tuple, Type

from skyweaver.core.bus.errors import DeliveryError
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.logistics.lifecycle import Lifecycle
from skyweaver.core.logistics.parcel import Parcel, EmptyParcel
from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.core.logistics.depot_messages import (
    DepotGet,
    DepotSet,
    DepotUpdate,
)
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from enum import Enum, auto
from typing import get_origin, get_args


class ParcelRole(Enum):
    """Role of a parcel in an Outpost."""
    CONSUMED = auto()   # dependency
    PRODUCED = auto()   # owned / produced here
    UNDEFINED = auto()  # undefined role

@dataclass
class Outpost:
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

    

    _transaction_open: bool = field(default=True, init=False, repr=False)
    _publisher_id: int = field(default=-1, init=False, repr=False)

    # ------------------------------------------------------------------
    # Initialization & lifecycle
    # ------------------------------------------------------------------

    def __post_init__(self):
        # Infrastructure
        self._message_hub = MessageHub()
        self._publisher_id = self._message_hub.register_publisher(owner=self)

        # Parcel roles
        self._roles = self._parcel_roles()
        consumed: Set[Type[Parcel]] = {
            parcel_type
            for parcel_type, role in self._roles.items()
            if role == ParcelRole.CONSUMED
        }

        # Lifecycle (semantic state)
        self._lifecycle = Lifecycle(
            publisher_id=self._publisher_id,
            message_hub=self._message_hub,
            dependencies=consumed,
        )

        self.dependencies_satisfied: Set[Type[Parcel]] = set()

        self._lifecycle.notify_join()

        # Subscriptions (reactive updates)
        self._message_hub.subscribe(
            topic=TopicsEnum.DEPOT_GET,
            publisher_id=self._publisher_id,
            subscriber=self._on_parcel_update,
            post_subscriber=self._on_post_event
        )

        self._message_hub.subscribe(
            topic=TopicsEnum.DEPOT_SET,
            publisher_id=self._publisher_id,
            subscriber=self._on_parcel_update,
            post_subscriber=self._on_post_event
        )

        # Request ALL declared parcels (dependencies + optional state)

        self._request_parcels(types=set(self._roles.keys()))


        object.__setattr__(self, "_transaction_open", False)

    # ------------------------------------------------------------------
    # Parcel discovery
    # ------------------------------------------------------------------

    def _declared_parcels(self) -> Dict[str, Optional[Parcel]]:
        return {
            f.name: getattr(self, f.name)
            for f in fields(self)
            if isinstance(getattr(self, f.name), Parcel)
        }



    
    def _parcel_roles(self) -> Dict[Type[Parcel], ParcelRole]:
        roles: Dict[Type[Parcel], ParcelRole] = {}

        for f in fields(self):
            role = f.metadata.get("role")
            

            annotation = f.type
            origin = get_origin(annotation)

            if origin is Optional:
                parcel_type = get_args(annotation)[0]
            else:
                parcel_type = annotation

            if not isinstance(parcel_type, type):
                continue

            if issubclass(parcel_type, Parcel):
                if not role:
                    roles[parcel_type] = ParcelRole.UNDEFINED
                else:
                    roles[parcel_type] = role

        return roles

    # ------------------------------------------------------------------
    # Depot interaction
    # ------------------------------------------------------------------

    def _request_parcels(self, types: Set[Type[Parcel]]):
        self._message_hub.publish(
            topic=TopicsEnum.DEPOT_GET,
            message=DepotGet(types=list(types)),
            message_context=MessageContext(
                from_id=self._publisher_id,
                to_id=ReservedIDs.DEPOT.value,
            ),
        )


    # ------------------------------------------------------------------
    # Message handling (GET replies and SET broadcasts)
    # ------------------------------------------------------------------

    def _on_parcel_update(self, message: BaseMessage, context: MessageContext):
        if context.from_id == self._publisher_id:
            print("[Outpost] Ignoring update from self")
            return

        if not isinstance(message, DepotUpdate):
            print("[Outpost] Ignoring non-DepotUpdate message")
            return

        pallet = message.pallet
        dependencies_satisfied: set[type[Parcel]] = set()

        for f in fields(self):
            role = f.metadata.get("role")
            #if role is None:
            #    continue

            annotation = f.type
            origin = get_origin(annotation)

            if origin is Optional:
                parcel_type = get_args(annotation)[0]
            else:
                parcel_type = annotation

            if parcel_type not in pallet:
                continue

            incoming = pallet[parcel_type]

            if isinstance(incoming, EmptyParcel):
                continue

            object.__setattr__(self, f.name, incoming)

            if role == ParcelRole.CONSUMED:
                dependencies_satisfied.add(parcel_type)

        #self.dependencies_satisfied = dependencies_satisfied
        object.__setattr__(self, "dependencies_satisfied", dependencies_satisfied)

        

    def _on_post_event(self, message: BaseMessage, context: MessageContext, delivered: bool):
        """
        All Outpost ↔ Depot interactions are synchronous and authoritative.
        Any message that is not delivered invalidates the operation and must raise an error.        
        """

        if not delivered:
            raise DeliveryError()
            #pass

        if self.dependencies_satisfied:
            self._lifecycle.mark_dependencies_satisfied(self.dependencies_satisfied)
        self._lifecycle.verify_and_notify()
    # ------------------------------------------------------------------
    # Controlled mutation
    # ------------------------------------------------------------------

    def __setattr__(self, name, value):
        if not getattr(self, "_transaction_open", False):
            raise AttributeError(
                "Direct assignment is disabled. "
                "Use 'with Outpost() as outpost:'"
            )
        object.__setattr__(self, name, value)

    # ------------------------------------------------------------------
    # Transaction context
    # ------------------------------------------------------------------

    def __enter__(self):
        print("[Outpost] Beginning transaction")
        object.__setattr__(self, "_transaction_open", True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                print("[Outpost] Committing transaction")
                pallet = {
                    type(parcel): parcel
                    for parcel in self._declared_parcels().values()
                    if parcel is not None
                }
                print("[Outpost] Prepared pallet for Depot:", pallet)
                if pallet:
                    print("[Outpost] Publishing updated parcels to Depot:", pallet)
                    self._message_hub.publish(
                        topic=TopicsEnum.DEPOT_SET,
                        message=DepotSet(pallet=pallet),
                        message_context=MessageContext(
                            from_id=self._publisher_id,
                            to_id=ReservedIDs.DEPOT.value,
                        ),
                    )
        finally:
            object.__setattr__(self, "_transaction_open", False)
            print("[Outpost] Transaction closed")


 # ------------------------------------------------------------------
# TODO: KEEP REFACTORING BELOW
# ------------------------------------------------------------------


@dataclass
class ParcelSchema:

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
    
class BaseOperationEvent:
    pass

class OperationStarted(BaseOperationEvent):
    pass

class OperationCompleted(BaseOperationEvent):
    pass


class ParcelDepotSyncer:
    def __init__(
        self,
        on_pallet_begin: Callable[[Dict[Type[Parcel], Parcel]], None],
        on_pallet_end: Callable[[], None],
    ):
        self._on_pallet_begin = on_pallet_begin
        self._on_pallet_end = on_pallet_end
        
        self._message_hub = MessageHub()
        self._publisher_id = self._message_hub.register_publisher(owner=self)

        self._message_hub.subscribe(
            topic=TopicsEnum.DEPOT_GET,
            publisher_id=self._publisher_id,
            subscriber=self._on_incoming_update,
            post_subscriber=self._on_post_update,
        )

        self._message_hub.subscribe(
            topic=TopicsEnum.DEPOT_SET,
            publisher_id=self._publisher_id,
            subscriber=self._on_incoming_update,
            post_subscriber=self._on_post_update,
        )

    def send_parcels_to_depot_to_update(self, pallet: Dict[Type[Parcel], Parcel]):
        self._message_hub.publish(
            topic=TopicsEnum.DEPOT_SET,
            message=DepotSet(pallet=pallet),
            message_context=MessageContext(
                from_id=self._publisher_id,
                to_id=ReservedIDs.DEPOT.value,
            ),
        )

    def request_updated_parcels(self, types: Set[Type[Parcel]]):
        self._message_hub.publish(
            topic=TopicsEnum.DEPOT_GET,
            message=DepotGet(types=list(types)),
            message_context=MessageContext(
                from_id=self._publisher_id,
                to_id=ReservedIDs.DEPOT.value,
            ),
        )

    def _on_incoming_update(self, message, context):
        if self._should_ignore(message, context):
            return
        self._on_pallet_begin(cast(DepotUpdate, message).pallet)


    def _on_post_update(self, message, context, delivered: bool):
        if self._should_ignore(message, context):
            return
        self._on_pallet_end()

    def _should_ignore(self, message, context) -> bool:
        if context.from_id == self._publisher_id:
            return True

        if not isinstance(message, DepotUpdate):
            return True

        return False


class OutpostOperationalStates(Enum):
    IDLE = auto()
    BUSY = auto()
    ERROR = auto()
    ON_UPDATE = auto()

    ON_SENDING_TO_DEPOT = auto()
    ON_RECEIVING_FROM_DEPOT = auto()

    BEGINNING_OPERATION = auto()
    COMPLETING_OPERATION = auto()
    TRANSACTION = auto()


@dataclass(frozen=True)
class StateFlags:
    _block_updates: bool
    

@dataclass
class BaseReactive(ParcelSchema):
    "Máquina Reativa Orientada a Eventos QUE ESCOLHE O ESTADO MAIS ADEQUADO A CADA EVENTO"
    #TODO: futuro outpost reativo
    

    def __post_init__(self):
        OutpostOperationalStates.BEGINNING_OPERATION
        self._end_event()

    def _on_update(self):
        OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT
        self._end_event()

    def __enter__(self):
        OutpostOperationalStates.TRANSACTION
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        OutpostOperationalStates.ON_SENDING_TO_DEPOT
        self._end_event()

    def _end_event(self):
        OutpostOperationalStates.IDLE

    def _set_parcels(self, parcel):
        pass

    def _transition_state(self, new_state: OutpostOperationalStates):
        if new_state == OutpostOperationalStates.IDLE:
            self._flags = StateFlags(_block_updates = False)
        if new_state == OutpostOperationalStates.TRANSACTION:
            self._flags = StateFlags(_block_updates = True)
