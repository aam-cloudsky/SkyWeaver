from typing import (
    Callable,
    ClassVar,
    Dict,
    Any,
    Optional,
    cast,
)
from dataclasses import InitVar, dataclass, field, fields
import warnings

from skyweaver.core.bus.bus import Bus


from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.identifier.identifier import LogisticsId, NodeId, OutpostId
from skyweaver.core.logistics.depot_messages import (
    DepotGet,
    DepotRegistry,
    DepotSet,
    DepotUpdate,
)


from skyweaver.core.logistics.endpoint.schema import SchemaBuilder
from skyweaver.core.logistics.endpoint.status.status import Status
from skyweaver.core.logistics.endpoint.status.status_manager import StatusManager
from skyweaver.core.logistics.lifecycle import LifecycleState, LifecycleStateMessage

from skyweaver.core.logistics.parcel.parcel import Parcel

from enum import Enum, auto

from typing import Optional, TypeAlias, cast

ParcelType: TypeAlias = type[Parcel]

DependencyChangeCount: TypeAlias = tuple[int, int]
ParcelPallet: TypeAlias = dict[ParcelType, Parcel]

ConsumedPallet: TypeAlias = dict[ParcelType, Parcel]
ProducedPallet: TypeAlias = dict[ParcelType, Parcel]

InconsistencyHandler: TypeAlias = Callable[[], None]


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
    _permit_dynamic_attribute_creation: bool


@dataclass(eq=False)
class Outpost(SchemaBuilder):
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

    node_id: NodeId
    logistics_id: LogisticsId

    _STATE_FLAG_MAP: ClassVar[Dict[OutpostOperationalStates, StateFlags]] = {
        OutpostOperationalStates.IDLE: StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=False,
            _permit_internal_private_mutation=False,
            _permit_dynamic_attribute_creation=False,
        ),
        OutpostOperationalStates.TRANSACTION: StateFlags(
            _permit_external_parcels_mutation=True,
            _permit_internal_parcel_mutation=True,
            _permit_internal_private_mutation=True,
            _permit_dynamic_attribute_creation=False,
        ),
        OutpostOperationalStates.BEGINNING_OPERATION: StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=True,
            _permit_internal_private_mutation=True,
            _permit_dynamic_attribute_creation=False,
        ),
        OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT: StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=True,
            _permit_internal_private_mutation=True,
            _permit_dynamic_attribute_creation=False,
        ),
    }

    bus: InitVar[Bus] = field(kw_only=True)

    _identity: OutpostId = field(
        init=False,
        repr=False,
    )

    _state: OutpostOperationalStates = field(
        init=False,
        repr=False,
    )

    # =======================================================
    # Operational State Management
    # =======================================================

    def __post_init__(
        self,
        bus: Bus,
    ) -> None:
        """
        Reactive configuration unit synchronized via Depot.

        - Declares Parcels as dataclass fields
        - CONSUMED Parcels are dependencies
        - PRODUCED Parcels are published after transactions

        Field semantics
        ---------------
        Declared Parcel fields may temporarily hold `None`.

        In the current runtime, `None` means that the corresponding Parcel is
        not currently available in this Outpost: it has not yet been received
        from the Depot or has not yet been produced locally.

        This is a runtime availability state, not a Parcel state.

        Therefore, the system distinguishes between:

        - `None`:
          no Parcel is currently available for that field
        - `Parcel(...)`:
          a concrete Parcel instance is available
        - a published Parcel with provenance/version:
          a Parcel that has already been committed through the runtime

        Absence is represented by `None`, not by a special empty Parcel instance.

        NOTE:
        This system assumes strong synchronization.
        Delivery failure indicates incorrect usage or initialization order.
        Local state is not rolled back on failed delivery.
        """

        self._setup_declared_fields()
        self._init_flags()
        self._transition_state(OutpostOperationalStates.BEGINNING_OPERATION)

        self._identity: OutpostId = OutpostId(
            name=self.__class__.__name__, logistics=self.logistics_id, node=self.node_id
        )
        self._bus = bus

        self._status_manager = StatusManager(
            self._schema.descriptors,
        )
        self._setup_ports()

        # self._request_pallet()

    def start(self) -> None:
        self._register_with_depot()

    def _setup_declared_fields(self):
        object.__setattr__(self, "_declared_fields", {f.name for f in fields(self)})

    def _init_flags(self):
        self._flags: StateFlags = StateFlags(
            _permit_external_parcels_mutation=False,
            _permit_internal_parcel_mutation=False,
            _permit_internal_private_mutation=True,
            _permit_dynamic_attribute_creation=False,
        )

    def _notify(self, state: LifecycleState):
        if getattr(self, "_last_lifecycle_state", None) != state:

            self._lifecycle_port.send(LifecycleStateMessage(state=state))
            self._last_lifecycle_state = state

    @property
    def identity(self) -> OutpostId:
        return self._identity

    # =======================================================
    # Port Operations
    # =======================================================

    def _setup_ports(self) -> None:
        self._registry_port = self._bus.port(
            owner=self,
            topic=TopicsEnum.DEPOT_REGISTRY,
            on_arrive=self._on_registry_arrive,
            on_end_arrive=self._on_registry_arrive_end,
        )

        self._set_port = self._bus.port(
            owner=self,
            topic=TopicsEnum.DEPOT_SET,
            on_arrive=self._on_pallet_arrive,
            on_end_arrive=self._on_pallet_end,
        )

        self._get_port = self._bus.port(
            owner=self,
            topic=TopicsEnum.DEPOT_GET,
            on_arrive=self._on_get_pallet_arrive,
            on_end_arrive=self._on_get_pallet_end,
        )

        self._lifecycle_port = self._bus.port(
            owner=self,
            topic=TopicsEnum.LIFECYCLE,
        )

        # self._register_with_depot()

    def _register_with_depot(self) -> None:
        self._registry_port.send(
            DepotRegistry(
                outpost_type=type(self),
                parcels_by_role=self._schema.types_by_role,
                # producer_path=f"{self.identity.node.flow.name}.{self.identity.node.name}",
            )
        )

    def _on_registry_arrive(self, message: BaseMessage, context: MessageContext):
        self._transition_state(OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT)
        depot_registry = cast(DepotRegistry, message)
        return depot_registry.registered

    def _on_registry_arrive_end(self, result: Any):
        registered = result
        if registered:
            self._notify(LifecycleState.JOINED)
            self._request_pallet()
        else:
            self._notify(LifecycleState.FAILED_TO_JOIN)

        self._transition_state(OutpostOperationalStates.IDLE)

    def _on_get_pallet_arrive(self, message: BaseMessage, context: MessageContext):
        self._transition_state(OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT)
        return self._on_pallet_arrive(message, context)

    def _on_get_pallet_end(self, result):
        self._notify(LifecycleState.SYNCED)
        self._on_pallet_end(result)

        # self._transition_state(OutpostOperationalStates.IDLE)

    # =======================================================
    # On Pallet Management
    # =======================================================

    def _request_pallet(self) -> None:
        self._get_port.send(DepotGet(types=list(self._schema.types())))

    def _on_pallet_arrive(self, message: BaseMessage, context: MessageContext):
        """
        Split Phase call. This is the phase 'processing'. No colaterals (callbacks) should be here.
        """
        self._transition_state(OutpostOperationalStates.ON_RECEIVING_FROM_DEPOT)
        mes = cast(DepotUpdate, message)
        return self._set_parcels(
            mes.pallet,
        )

    def _on_pallet_end(self, status_updated):
        """
        Split Phase call. This is the phase 'post_processing'. Colaterals (callbacks) should be here.
        """

        if status_updated:
            _on_status_changed: Callable[[Status[ParcelType]], None] = getattr(
                self, "_on_status_changed", lambda change_statue: None
            )
            _on_status_changed(
                self._status_manager.status,
            )

        self._transition_state(OutpostOperationalStates.IDLE)

    def set_on_status_changed(
        self,
        callback: Callable[[Status[ParcelType]], None],
    ) -> None:
        object.__setattr__(
            self,
            "_on_status_changed",
            callback,
        )

    def _commit_pallet(
        self,
        produced: dict[ParcelType, Parcel],
    ) -> None:

        for parcel_type, parcel in produced.items():

            self._update_provenance(
                parcel_type,
                parcel,
            )

        self._set_port.send(
            DepotSet(
                pallet=produced,
            )
        )

    # =======================================================
    # Provenance Update
    # =======================================================

    def _get_previous_parcel(
        self,
        parcel_type: ParcelType,
    ) -> Optional[Parcel]:

        previous_parcels = getattr(
            self,
            "_produced_parcel_snapshot",
            {},
        )

        return previous_parcels.get(parcel_type)

    def _update_provenance(
        self,
        parcel_type: ParcelType,
        parcel: Parcel,
    ) -> None:

        parcel.record_origin(
            node_id=self._identity.node,
            previous=self._get_previous_parcel(parcel_type),
            dependencies=self.dependency_versions_of(
                parcel_type,
            ),
        )

    def _save_produced_parcel_snapshot(self) -> None:

        object.__setattr__(
            self,
            "_produced_parcel_snapshot",
            {
                parcel_type: parcel
                for parcel_type, parcel in self.produced_parcels().items()
            },
        )

    def _clear_produced_parcel_snapshot(self) -> None:

        object.__setattr__(
            self,
            "_produced_parcel_snapshot",
            {},
        )

    # =======================================================
    # Transaction Context
    # =======================================================

    def __enter__(self):
        self._save_produced_parcel_snapshot()
        self._transition_state(OutpostOperationalStates.TRANSACTION)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            produced: dict[ParcelType, Parcel] = self.produced_parcels()

            if not produced:
                return

            self._commit_pallet(produced)

            for p in produced:
                self._status_manager.mark_clean(p)

        finally:

            self._clear_produced_parcel_snapshot()
            self._transition_state(OutpostOperationalStates.IDLE)

    def _transition_state(self, new_state: OutpostOperationalStates):
        """
        All state transitions must update flags accordingly.
        1. IDLE: no parcel changes allowed
        """
        # self._state = new_state
        # self._flags = self._STATE_FLAG_MAP[new_state]

        object.__setattr__(self, "_flags", self._STATE_FLAG_MAP[new_state])
        object.__setattr__(self, "_state", new_state)

    # ======================================================
    # Flagged Functions
    # set parcels must only works within permitted contexts
    # it is blocked by __setattr__
    # =======================================================

    def _set_parcels(
        self,
        pallet: ParcelPallet,
    ) -> bool:
        if not self._flags._permit_internal_parcel_mutation:
            raise RuntimeError(
                "_set_parcels called while internal Parcel mutation "
                "is not permitted. "
                f"Outpost: '{type(self).__module__}.{type(self).__qualname__}'. "
                f"Operational state: '{self._state.name}'."
            )

        status_changed = False
        for parcel_type, parcel in pallet.items():
            descriptor = self._schema.descriptors.get(
                parcel_type,
            )

            if descriptor is None:
                continue

            current = self.parcel(parcel_type)
            if current is None or current.version != parcel.version:
                status_changed |= self._status_manager.mark_dirty(parcel_type)

            object.__setattr__(
                self,
                descriptor.field_name,
                parcel,
            )

        return status_changed

    def _build_pallet(self) -> ParcelPallet:
        pallet: ParcelPallet = {}

        for parcel_type in self._schema.types():
            parcel = self.parcel(
                parcel_type,
            )

            if parcel is not None:
                pallet[parcel_type] = parcel

        return pallet

    def __setattr__(self, name, value):
        """
        CORE mutation gate.

        Explicit rules:
        1) During init (before policy exists), allow assignment.
        2) If name is not declared and dynamic creation is forbidden -> error.
        3) Private attributes ('_x') obey internal_private_write policy.
        4) Declared parcel fields obey external_parcel_write policy.
        5) Declared non-parcel fields are also blocked externally by default
           (unless you decide otherwise explicitly).
        """

        # -------------------------------------------------
        # Allow normal attribute setting during init
        # -------------------------------------------------

        # Durante __init__ / __post_init__, _flags ainda não existe
        if not hasattr(self, "_flags"):
            object.__setattr__(self, name, value)
            return

        # -------------------------------------------------
        # Block dynamic attribute creation
        # -------------------------------------------------

        if (
            not name.startswith("_")
            and hasattr(self, "_declared_fields")
            and name not in self.__getattribute__("_declared_fields")
            and not self._flags._permit_dynamic_attribute_creation
        ):
            raise AttributeError(
                f"'{type(self).__name__}' has no declared field '{name}'. "
                "Dynamic attribute creation is not allowed."
            )

        # -------------------------------------------------
        # Internal private mutation (controlled)
        # -------------------------------------------------
        if name.startswith("_") and self._flags._permit_internal_private_mutation:
            object.__setattr__(self, name, value)
            return

        # -------------------------------------------------
        # External parcel mutation (transaction context)
        # -------------------------------------------------
        if self._flags._permit_external_parcels_mutation:
            object.__setattr__(self, name, value)
            return

        # -------------------------------------------------
        # Otherwise: forbidden
        # -------------------------------------------------
        raise AttributeError(
            "Direct assignment is disabled. " "Use 'with Outpost() as outpost:'"
        )

    def close(self) -> None:
        ports = (
            "_registry_port",
            "_set_port",
            "_get_port",
            "_lifecycle_port",
        )

        publisher_id = None

        for port_name in ports:
            port = getattr(self, port_name, None)
            if port is None:
                continue

            if publisher_id is None:
                publisher_id = getattr(port, "_publisher_id", None)

        if publisher_id is not None:
            self._bus._hub.unregister_owner(publisher_id)
