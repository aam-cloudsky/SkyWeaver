# src/skyweaver/scenarios/components/cluster/cluster.py
from dataclasses import dataclass
from shapely.geometry import Point, Polygon
from skyweaver.units.clustering.zone_type import ZoneType


@dataclass
class Cluster:
    """Encapsulates a UAV or MAV cluster within the airspace."""

    source_points: list[Point]
    zone_type: ZoneType
    centroid: Point
    polygon: Polygon
    boundary: list[Point]
    _boundary_max_distance: float = 0.0

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

    def farthest_boundary(self) -> float:
        """Return the radius to point in the boundary farthest from the centroid."""

        if self._boundary_max_distance > 0:
            return self._boundary_max_distance

        max_dist = 0

        for point in self.boundary:
            dist = self.centroid.distance(point)
            if dist > max_dist:
                max_dist = dist

        self._boundary_max_distance = max_dist
        return max_dist

    @property
    def boundary_max_distance(self) -> float:
        if self._boundary_max_distance > 0:
            return self._boundary_max_distance

        self._boundary_max_distance = self.farthest_boundary()
        return self._boundary_max_distance
