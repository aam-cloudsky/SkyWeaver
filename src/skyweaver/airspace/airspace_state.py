# src/skyweaver/airspace/airspace_state.py

from typing import Any, Callable, Dict, List, Optional, Tuple, cast
import threading
from shapely import Point
from skyweaver.core.bus.messages.airspace_message import ComponentGet, ComponentSet, ComponentUpdate
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.null_grid import NullGrid
from skyweaver.instance_segmentation.geometry.cluster import Cluster
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell
import networkx as nx

from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.airspace.base_component import BaseComponent, NullComponent




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
class AirspaceState(metaclass=ThreadSingleton):
    """Centralized singleton data registry for the SkyWeaver simulation.
    Holds all spatial entities and notifies listeners when updated.
    """

    def __init__(self):

        self._components: Dict[type, BaseComponent] = {}
        self._null_component = NullComponent()

        # Primary points of interest
        self.uav_points: List[Point] = []
        self.mav_points: List[Point] = []

        # Cluster-level information
        self.clusters: List[Cluster] = []

        # Grid
        self.grid: BaseGrid = NullGrid()

        # Voronoi and environment geometry
        self.voronoi_cells: List[VoronoiCell] = []
        self.adjacency_graph: nx.Graph = nx.Graph()

        # Metadata
        self.domain: Tuple[Tuple[float, float], Tuple[float, float]] = (
            (-1000, 1000),
            (-1000, 1000),
        )
        self.seed: Optional[int] = None
        self.step: int = 0

        # Reactive callbacks
        self._on_update: Dict[str, List[Callable]] = {}

        self.publisher_id = ReservedIDs.AIRSPACE_STATE.value
        self.message_hub: MessageHub = MessageHub()
        self._subscribe_to_topics()

    # ------------------------------------------------------------------
    # Component Management
    # ------------------------------------------------------------------

    def get_component(self, component_type: type[BaseComponent]) -> BaseComponent:
        return self._components.get(component_type, self._null_component)

    def set_component(self, component: BaseComponent):
        if not isinstance(component, BaseComponent):
            raise TypeError("Only BaseComponent instances can be registered")

        self._components[type(component)] = component

    def _broadcast_component_update(self, component: BaseComponent):
        print(
            f"[AIRSPACE STATE] _broadcast_component_update Broadcasting ComponentUpdate: "
            f"{type(component).__name__} | "
            f"id={id(component)}"
        )
        MessageHub().publish(
            topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
            message=ComponentUpdate(component=component),
            message_context=MessageContext(
                from_id=self.publisher_id,
                to_id=ReservedIDs.BROADCAST.value,
            )
        )

    def _on_component_request(self, message: BaseMessage, context: MessageContext):
        
            
        if isinstance(message, ComponentGet):
            
            mes: ComponentGet = cast(ComponentGet, message)
            component = self.get_component(mes.component_type)

            print(
                f"[AIRSPACE STATE] _on_component_request Received ComponentGet: "
                f"{type(component).__name__} | "
                f"id={id(component)}"
            )


            self.message_hub.publish(
                topic=TopicsEnum.AIRSPACE_STATE_GET,
                message=ComponentUpdate(component=component),
                message_context=MessageContext(
                    from_id=self.publisher_id,
                    to_id=context.from_id
                )
            )

        elif isinstance(message, ComponentSet):
            self.set_component(message.component)

            print(
                f"[AIRSPACE STATE] _on_component_request Received ComponentSet: "
                f"{type(message.component).__name__} | "
                f"id={id(message.component)}"
            )

            self._broadcast_component_update(message.component)

            

    # ------------------------------------------------------------------
    # MessageHub Registration and Subscription
    # ------------------------------------------------------------------

    def _subscribe_to_topics(self):
        """Subscribe to relevant MessageHub topics."""

        self.message_hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_GET,
            publisher_id=self.publisher_id,
            subscriber=self._on_component_request
        )


        self.message_hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
            publisher_id=self.publisher_id,
            subscriber=self._on_component_request
        )