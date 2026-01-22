# src/skyweaver/airspace/airspace_state.py
from dataclasses import fields
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading
from shapely import Point
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.null_grid import NullGrid
from skyweaver.instance_segmentation.geometry.cluster import Cluster
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell
import networkx as nx

from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext

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
    # MessageHub Registration and Subscription
    # ------------------------------------------------------------------

    def _subscribe_to_topics(self):
        """Subscribe to relevant MessageHub topics."""


        self.message_hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_GET,
            publisher_id=self.publisher_id,
            subscriber=self._on_airspace_get
        )

        self.message_hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
            publisher_id=self.publisher_id,
            subscriber=self._on_airspace_update
        )

    def _on_airspace_get(self, message: Dict, context: MessageContext):
        """Handle AIRSPACE_STATE_GET requests.

        The message is a dict like:
            {"uav_points": None, "mav_points": None, "clusters": None}

        The values are placeholders and are ignored — only keys matter.
        AirspaceState responds with a dict mapping each requested field to its current value.
        """
        response = {}
        for field_name in message.keys():
            if hasattr(self, field_name):
                response[field_name] = getattr(self, field_name)

        # Send the current values back to the requester
        response_context = MessageContext(
            from_id=self.publisher_id,
            to_id=context.from_id
        )

        self.message_hub.publish(
            topic=TopicsEnum.AIRSPACE_STATE_GET,
            message=response,
            message_context=response_context
        )


    def _on_airspace_update(self, message: Dict, context: MessageContext):
        """Handle AIRSPACE_STATE_UPDATE requests."""

        changes = message

        if not changes:
            return

        applied = self.update_state(**changes)
        self._broadcast_state_update(applied, context)

    def _broadcast_state_update(self, changes: Dict[str, Any], origin_context: MessageContext):
        """Broadcast state updates to interested parties."""
        
        response_context = MessageContext(
            from_id=self.publisher_id,
            to_id=ReservedIDs.BROADCAST.value,
            exclude_ids=[origin_context.from_id]
        )

        self.message_hub.publish(
            topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
            message=changes,
            message_context=response_context
        )

    # ------------------------------------------------------------------
    # Core state management
    # ------------------------------------------------------------------
    def update_state(self, **changes):
        applied = {}
        for attr, new_value in changes.items():
            if hasattr(self, attr):
                setattr(self, attr, new_value)
                applied[attr] = new_value
            
        return applied

    def increment_step(self):
        """Advance the simulation step counter."""
        self.step += 1

    def reset(self):
        """Completely reset dynamic contents (except callbacks)."""
        self.uav_points.clear()
        self.mav_points.clear()
        self.clusters.clear()
        self.voronoi_cells.clear()
        self.step = 0

    def to_json(self) -> Dict[str, Any]:
        """Serialize the current state to a JSON-compatible dictionary."""

        variables =  {key: value for key, value in self.__dict__.items()
                           if not callable(value) and not key.startswith('__')}

        
        #remove empty keys
        variables = {key: value for key, value in variables.items() if value}

        return variables
