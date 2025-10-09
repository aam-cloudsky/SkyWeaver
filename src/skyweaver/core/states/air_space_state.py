
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from skyweaver.core.geometry.point import Point


import threading
from dataclasses import dataclass
from typing import List, Tuple
from skyweaver.core.geometry.point import Point


class ThreadSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        tid = threading.get_ident()
        if (cls, tid) not in cls._instances:
            cls._instances[(cls, tid)] = super(
                ThreadSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[(cls, tid)]

@dataclass
class AirspaceState(metaclass=ThreadSingleton):
    """Centralized singleton data registry for the SkyWeaver simulation."""

    storage: dict = field(default_factory=dict)
    
    # Primary points of interest
    uav_points: List[Point] = field(default_factory=list)
    mav_points: List[Point] = field(default_factory=list)

    # Cluster-level information
    centroids: List[Point] = field(default_factory=list)
    cluster_polygons: Dict[str, List[Point]] = field(default_factory=dict)

    # Voronoi and environment geometry
    voronoi_cells: Dict[str, List[Point]] = field(default_factory=dict)
    bounding_polygon: Optional[List[Point]] = None

    # Metadata
    domain: Tuple[Tuple[float, float], Tuple[float, float]] = ((-1000, 1000), (-1000, 1000))
    seed: Optional[int] = None
    step: int = 0
    _last_update: dict[str, float] = field(default_factory=dict)

    def increment_step(self):
        """Advance the simulation step counter."""
        self.step += 1

    def _mark_update(self, attribute: str):
        """Record the current step as the last update for the given attribute."""
        self._last_update[attribute] = self.step

    def reset(self, view_name: str, params: dict):
        """Reset the state for a specific view."""
        self.storage[view_name] = params
        self._mark_update(view_name)



    def reset_distribution(self):
        """Clear only distribution-related data (UAV/MAV points and domain)."""
        self.uav_points.clear()
        self.mav_points.clear()
        self.domain = ((-1000, 1000), (-1000, 1000))

        self._mark_update("distribution")


    def reset_clusters(self):
        """Clear cluster and centroid data."""
        self.centroids.clear()
        self.cluster_polygons.clear()

        self._mark_update("clusters")


    def reset_voronoi(self):
        """Clear Voronoi-related structures."""
        self.voronoi_cells.clear()
        self.bounding_polygon = None

        self._mark_update("voronoi")


    def reset_all(self):
        """Clear everything (for a full simulation restart)."""
        self.reset_distribution()
        self.reset_clusters()
        self.reset_voronoi()
        self.step = 0


    def summary(self) -> str:
        return (
            f"AirspaceState Summary\n"
            f"----------------------\n"
            f"Domain: {self.domain}\n"
            f"Seed: {self.seed}\n"
            f"Step: {self.step}\n"
            f"UAV Points: {len(self.uav_points)}\n"
            f"MAV Points: {len(self.mav_points)}\n"
            f"Centroids: {len(self.centroids)}\n"
            f"Voronoi Cells: {len(self.voronoi_cells)}\n"
        )
