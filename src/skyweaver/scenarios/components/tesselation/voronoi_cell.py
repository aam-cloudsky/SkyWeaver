# src/skyweaver/scenarios/components/voronoi/voronoi_cell.py
from dataclasses import dataclass, field
from typing import Dict, List
from shapely import Point, Polygon
from shapely.ops import unary_union

from skyweaver.scenarios.components.cluster.cluster_configuration import ClusterConfiguration
from skyweaver.core.enums.zone_type import ZoneType


@dataclass
class VoronoiCell:
    """Represents a single Voronoi cell in the airspace."""
    id: str
    seed_point: Point
    polygon: Polygon
    vertices: List[Point] = field(default_factory=list)
    validity: bool = True

    # --- overlap thresholds ---
    mav_threshold: float = 0.2  # 20% max MAV occupation

    # --- overlap tracking ---
    cluster_intersections: Dict[str, float] = field(default_factory=dict)
    total_overlap_area: float = 0.0
    mav_overlap_area: float = 0.0
    uav_overlap_area: float = 0.0
    mav_overlap_ratio: float = 0.0
    uav_overlap_ratio: float = 0.0

    def update_validity(self) -> None:
        """Recalculate validity and overlap metrics with MAV priority and non-overlapping unions."""
        cluster_config = ClusterConfiguration()
        self.cluster_intersections.clear()

        cell_area = self.polygon.area
        if cell_area <= 0:
            self.validity = False
            return

        # --- Step 1: collect intersection polygons ---
        uav_intersections = []
        mav_intersections = []

        for cid, cluster_polygon in cluster_config.polygons.items():
            if not cluster_polygon.intersects(self.polygon):
                continue
            intersection = self.polygon.intersection(cluster_polygon)
            if intersection.is_empty:
                continue

            self.cluster_intersections[cid] = intersection.area
            cluster_type = ZoneType.MAV if "MAV" in cid.upper() else ZoneType.UAV
            if cluster_type == ZoneType.MAV:
                mav_intersections.append(intersection)
            else:
                uav_intersections.append(intersection)

        # --- Step 2: merge same-type overlaps ---
        mav_union = unary_union(
            mav_intersections) if mav_intersections else None
        uav_union = unary_union(
            uav_intersections) if uav_intersections else None

        # --- Step 3: apply MAV priority ---
        # Subtract MAV-covered regions from UAV region
        if uav_union and mav_union:
            uav_union = uav_union.difference(mav_union)

        # --- Step 4: compute effective occupied areas ---
        self.mav_overlap_area = mav_union.area if mav_union else 0.0
        self.uav_overlap_area = uav_union.area if uav_union else 0.0
        self.total_overlap_area = self.mav_overlap_area + self.uav_overlap_area

        # --- Step 5: compute ratios and validity ---
        self.mav_overlap_ratio = self.mav_overlap_area / cell_area
        self.uav_overlap_ratio = self.uav_overlap_area / cell_area
        self.validity = self.mav_overlap_ratio < self.mav_threshold

    def to_points(self) -> List[Point]:
        """Return polygon vertices as list of Points."""
        return [Point(x, y) for x, y in self.polygon.exterior.coords]
