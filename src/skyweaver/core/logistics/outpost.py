from dataclasses import dataclass, field, fields
from skyweaver.core.logistics.lifecycle import Lifecycle
from skyweaver.core.logistics.parcel import Parcel, EmptyParcel
from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.core.logistics.depot_messages import (
    DepotGet,
    DepotSet,
    DepotUpdate,
)
from skyweaver.core.bus.reserved_id_enum import ReservedIDs


@dataclass
class Outpost:
    """Reactive configuration mixin that syncs parcels with Depot."""

    _transaction_open: bool = field(default=True, init=False, repr=False)
    _publisher_id: int = field(default=-1, init=False, repr=False)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __post_init__(self):
        self._message_hub = MessageHub()
        self._publisher_id = self._message_hub.register_publisher(owner=self)
        self._lifecycle = Lifecycle(self._message_hub)
        self._lifecycle._lifecycle_ready(self._publisher_id)
        

        # Subscribe to parcel updates
        self._message_hub.subscribe(
            topic=TopicsEnum.DEPOT_GET,
            publisher_id=self._publisher_id,
            subscriber=self._on_parcel_update,
        )

        self._message_hub.subscribe(
            topic=TopicsEnum.DEPOT_SET,
            publisher_id=self._publisher_id,
            subscriber=self._on_parcel_update,
        )

        # Initial GET for declared parcels
        for parcel in self._declared_parcels():
            self._request_parcel(type(parcel))

        object.__setattr__(self, "_transaction_open", False)

        



    # ------------------------------------------------------------------
    # Parcel discovery
    # ------------------------------------------------------------------

    def _declared_parcels(self) -> list[Parcel]:
        return [
            getattr(self, f.name)
            for f in fields(self)
            if isinstance(getattr(self, f.name), Parcel)
        ]

    def _request_parcel(self, parcel_type: type[Parcel]):
        self._message_hub.publish(
            topic=TopicsEnum.DEPOT_GET,
            message=DepotGet(types=[parcel_type]),
            message_context=MessageContext(
                from_id=self._publisher_id,
                to_id=ReservedIDs.DEPOT.value,
            ),
        )

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    def _on_parcel_update(self, message, context):

        if context.from_id == self._publisher_id:
            return
    
        if not isinstance(message, DepotUpdate):
            return

        pallet = message.pallet

        for f in fields(self):
            current = getattr(self, f.name)

            if not isinstance(current, Parcel):
                continue

            parcel_type = type(current)
            if parcel_type not in pallet:
                continue

            incoming = pallet[parcel_type]

            # ⛔ Nunca sobrescrever com EmptyParcel
            if isinstance(incoming, EmptyParcel):
                continue

            object.__setattr__(self, f.name, incoming)


    # ------------------------------------------------------------------
    # Controlled mutation
    # ------------------------------------------------------------------

    def __setattr__(self, name, value):
        if not getattr(self, "_transaction_open", False):
            raise AttributeError(
                "Direct assignment is disabled. Use 'with Outpost() as outpost:'"
            )

        # Allow any assignment during transaction
        object.__setattr__(self, name, value)


    # ------------------------------------------------------------------
    # Context manager
    # - Do not mutate outside of a transaction
    # - after each transaction, publish SET for all declared parcels
    # ------------------------------------------------------------------

    def __enter__(self):
        object.__setattr__(self, "_transaction_open", True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        try:
            if exc_type is None:
                pallet = {
                    type(parcel): parcel
                    for parcel in self._declared_parcels()
                    if not isinstance(parcel, EmptyParcel)
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
