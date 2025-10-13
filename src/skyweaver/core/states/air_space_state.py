
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shapely import Polygon
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

    # Primary points of interest
    uav_points: List[Point] = field(default_factory=list)
    mav_points: List[Point] = field(default_factory=list)

    # Cluster-level information

    clusters: Dict[str, List[Point]] = field(default_factory=dict)


    centroids: Dict[str, Point] = field(default_factory=dict)
    boundaries: Dict[str, List[Point]] = field(default_factory=dict)
    polygons: Dict[str, Polygon] = field(default_factory=dict)
    types: Dict[str, str] = field(default_factory=dict)







    # Voronoi and environment geometry
    voronoi_cells: Dict[str, List[Point]] = field(default_factory=dict)
    bounding_polygon: Optional[List[Point]] = None

    # Metadata
    domain: Tuple[Tuple[float, float], Tuple[float, float]] = ((-1000, 1000), (-1000, 1000))
    seed: Optional[int] = None
    step: int = 0
    _last_update: dict = field(default_factory=dict)


    def update_state(self, source: str, **changes):
        """
        Apply attribute updates atomically with full traceability.
        """

        for attr, new_value in changes.items():
            if hasattr(self, attr):
                old_value = getattr(self, attr)
                setattr(self, attr, new_value)

                # Stamp metadata
                stamp = {
                    "step": self.step,
                    "source": source,
                    "attribute": attr,
                    "old_value": old_value,
                    "new_value": new_value,
                }
                self._last_update[attr] = stamp

            else:
                raise AttributeError(
                    f"AirspaceState has no attribute '{attr}'")
            


    def increment_step(self):
        """Advance the simulation step counter."""
        self.step += 1

    def _mark_update(self, attribute: str):
        """Record the current step as the last update for the given attribute."""
        self._last_update[attribute] = self.step

    def reset(self, view_name: str, params: dict):
        """Reset the state for a specific view."""
        self._mark_update(view_name)



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
