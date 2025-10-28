# src/skyweaver/airspace/airspace_state.py
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading
from shapely import Point
from skyweaver.instance_segmentation.geometry.cluster import Cluster
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell
import networkx as nx

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

    # ------------------------------------------------------------------
    # Core state management
    # ------------------------------------------------------------------
    def update_state(self, source: str, **changes):
        applied = {}
        for attr, new_value in changes.items():
            if hasattr(self, attr):
                setattr(self, attr, new_value)
                applied[attr] = new_value
            else:
                raise AttributeError(f"AirspaceState has no attribute '{attr}'")
        if applied:
            self._notify_listeners(source, applied)

    def _notify_listeners(self, source, changes):
        notified = set()
        for attr, new_value in changes.items():
            for cb in self._on_update.get(attr, []):
                if cb not in notified:
                    try:
                        cb(source, attr, new_value)
                        notified.add(cb)
                    except Exception as e:
                        print(f"[WARN] callback {cb} failed: {e}")





    # ------------------------------------------------------------------
    # Callback management
    # ------------------------------------------------------------------
    def add_callback(self, attribute: str, callback: Callable):
        """Register a callback to be called on any update."""

        if hasattr(self, attribute):
            if attribute not in self._on_update:
                self._on_update[attribute] = []
            if callback not in self._on_update[attribute]:
                self._on_update[attribute].append(callback)

    def remove_callback(self, attribute: str, callback: Callable):
        """Unregister a previously registered callback."""
        for callbacks in self._on_update.values():
            if callback in callbacks:
                callbacks.remove(callback)


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
