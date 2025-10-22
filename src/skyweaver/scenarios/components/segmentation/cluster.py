# src/skyweaver/scenarios/components/cluster/cluster.py
from dataclasses import dataclass
from shapely import Polygon
from shapely.geometry import Point
from skyweaver.core.enums.zone_type import ZoneType


@dataclass
class Cluster:
    """Encapsulates a UAV or MAV cluster within the airspace."""

    
    zone_type: ZoneType
    centroid: Point
    polygon: Polygon
    boundary: list[Point]

    # Optional metadata
    area: float = 0

    def __post_init__(self):
        self.area = self.polygon.area

    # --- Geometry utilities ---
    def overlaps(self, other_polygon: Polygon) -> bool:
        return self.polygon.overlaps(other_polygon)

    def intersection_area(self, other_polygon: Polygon) -> float:
        """Return the area of intersection between this cluster and another polygon."""
        return self.polygon.intersection(other_polygon).area

    def contains_point(self, p: Point) -> bool:
        """Check if a given point lies within the cluster polygon."""
        return self.polygon.contains(p)

    def to_dict(self) -> dict:
        """Compact representation for serialization/logging."""
        return {
            "zone_type": self.zone_type.name,
            "centroid": (self.centroid.x, self.centroid.y),
            "area": self.area,
        }
