# src/skyweaver/scenarios/components/tesselation/voronoi_cell.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

from skyweaver.instance_segmentation.geometry.cluster import Cluster
from skyweaver.core.enums.zone_type import ZoneType
from math import log2

@dataclass
class VoronoiCell:
    """Represents a single Voronoi cell in the airspace."""

    seed_point: Point
    polygon: Polygon
    vertices: list[Point] = field(default_factory=list)

    # --- Overlap bookkeeping ---
    cluster_overlaps: list[dict] = field(default_factory=list)
    total_overlap_area: float = 0.0
    mav_overlap_area: float = 0.0
    uav_overlap_area: float = 0.0
    mav_overlap_ratio: float = 0.0
    uav_overlap_ratio: float = 0.0


    entropy: float = 0.0


    # ====================================================
    # Update overlap metrics based on cluster geometry
    # ====================================================

    def update(self, clusters):
        """Update overlap metrics with given clusters."""
        self.update_overlap(clusters)
        self.update_entropy()

    def update_overlap(self, clusters: list[Cluster]) -> None:
        """
        Update overlap metrics with MAV priority.
        This version avoids hash requirements for Cluster objects.
        """
        self.cluster_overlaps.clear()

        cell_area = self.polygon.area
        if cell_area <= 0:
            self.validity = False
            return

        uav_intersections = []
        mav_intersections = []

        # --- Step 1: gather intersections ---
        for cluster in clusters:
            if not cluster.polygon.intersects(self.polygon):
                continue

            intersection = self.polygon.intersection(cluster.polygon)
            if intersection.is_empty:
                continue

            # Store overlap information in a list (instead of dict)
            self.cluster_overlaps.append({
                "cluster": cluster,
                "zone_type": cluster.zone_type,
                "area": intersection.area,
            })

            if cluster.zone_type == ZoneType.MAV:
                mav_intersections.append(intersection)
            elif cluster.zone_type == ZoneType.UAV:
                uav_intersections.append(intersection)

        # --- Step 2: merge same-type overlaps ---
        mav_union = unary_union(
            mav_intersections) if mav_intersections else None
        uav_union = unary_union(
            uav_intersections) if uav_intersections else None

        # --- Step 3: MAV priority — subtract MAV from UAV ---
        if uav_union and mav_union:
            uav_union = uav_union.difference(mav_union)

        # --- Step 4: compute effective occupied areas ---
        self.mav_overlap_area = mav_union.area if mav_union else 0.0
        self.uav_overlap_area = uav_union.area if uav_union else 0.0
        self.total_overlap_area = self.mav_overlap_area + self.uav_overlap_area

        # --- Step 5: compute ratios and validity ---
        self.mav_overlap_ratio = self.mav_overlap_area / cell_area
        self.uav_overlap_ratio = self.uav_overlap_area / cell_area

    def __str__(self) -> str:
        return f"({self.seed_point.x:.1f},{self.seed_point.y:.1f})"
    
    def update_entropy(self):
        """Compute the impurity of the cell based on entropy over zone-type composition (MAV, UAV, Free)."""

        cell_area = self.polygon.area
        if cell_area <= 0:
            return 0.0

        # effective occupied areas
        mav = self.mav_overlap_area
        uav = self.uav_overlap_area
        free = max(0.0, cell_area - (mav + uav))

        total = mav + uav + free
        if total == 0:
            return 0.0

        probs = [mav / total, uav / total, free / total]
        probs = [p for p in probs if p > 0]  # avoid log(0)

        self.entropy = -sum(p * log2(p) for p in probs)


