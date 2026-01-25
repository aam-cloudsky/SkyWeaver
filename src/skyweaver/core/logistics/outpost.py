from dataclasses import dataclass, field, fields
from typing import Dict, Optional, Set, Type

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


@dataclass
class Outpost:
    """
    Reactive configuration unit synchronized via Depot.

    - Declares parcels as dataclass fields
    - CONSUMED parcels are dependencies
    - PRODUCED parcels are published after transactions
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
            if f.metadata.get("role") is not None
        }



    
    def _parcel_roles(self) -> Dict[Type[Parcel], ParcelRole]:
        roles: Dict[Type[Parcel], ParcelRole] = {}

        for f in fields(self):
            role = f.metadata.get("role")
            if not role:
                continue

            annotation = f.type
            origin = get_origin(annotation)

            if origin is Optional:
                parcel_type = get_args(annotation)[0]
            else:
                parcel_type = annotation

            if not isinstance(parcel_type, type):
                continue

            if issubclass(parcel_type, Parcel):
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

    def _on_parcel_update(self, message, context):
        if context.from_id == self._publisher_id:
            return

        if not isinstance(message, DepotUpdate):
            return

        pallet = message.pallet
        dependencies_satisfied: set[type[Parcel]] = set()

        for f in fields(self):
            role = f.metadata.get("role")
            if role is None:
                continue

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

        self.dependencies_satisfied = dependencies_satisfied

        

    def _on_post_event(self, BaseMessage, MessageContext):
        print(self.dependencies_satisfied)
        print(BaseMessage)
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
        object.__setattr__(self, "_transaction_open", True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                pallet = {
                    type(parcel): parcel
                    for parcel in self._declared_parcels().values()
                    if parcel is not None
                }

                if pallet:
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
