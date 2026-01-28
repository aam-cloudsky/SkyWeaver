# src/skyweaver/scenarios/components/instance_segmentation/clustering/hdbscan_clustering.py

from __future__ import annotations
from typing import List, cast


import numpy as np
import hdbscan
from shapely.geometry import Point
import matplotlib.pyplot as plt


from skyweaver.core.enums.zone_type import ZoneType
from skyweaver.clustering.cluster import Cluster
from skyweaver.clustering.base_clustering import BaseClustering
from skyweaver.clustering.cluster_shape_builder import ClusterShapeBuilder
from skyweaver.clustering.logistics.cluster_outpost import ClusterOutpost



# ==========================================================
# HDBSCAN Clustering
# ==========================================================
class HDBSCANClustering(BaseClustering):
    """
    Density-based adaptive clustering for airspace segmentation.
    Uses HDBSCAN to detect UAV and MAV operational zones.
    """

    def __init__(self, min_cluster_size: int = 2, min_samples: int = 2):
        super().__init__()
        self.shape_builder = ClusterShapeBuilder()
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples


    # ------------------------------------------------------
    # Internal fitting routine
    # ------------------------------------------------------

    def _fit_few_points(self, points: List[Point], zone_type: ZoneType) -> List[Cluster]:
        """Handle case with too few points to cluster."""

        if not points:
            return []


        print(f"[INFO] Too few {zone_type} points ({len(points)}). Creating one cluster.")
        centroid = np.mean([[p.x, p.y] for p in points], axis=0)
        polygon = Point(*centroid).buffer(50)
        return [Cluster(
            source_points=points,
            zone_type=zone_type,
            centroid=Point(*centroid),
            polygon=polygon,
            boundary=[Point(x, y) for x, y in polygon.exterior.coords],
        )]
    
    def _build_cluster(self, source_points: list[Point], zone_type: ZoneType):

        arr = np.array([[p.x, p.y] for p in source_points])
        cx, cy = arr.mean(axis=0)
        centroid = Point(cx, cy)

        polygon = self.shape_builder.smooth_radial_boundary(
            centroid=centroid,
            source_points=source_points,
            offset=80.0
        )
        return Cluster(
            source_points=source_points,
            zone_type=zone_type,
            centroid=centroid,
            polygon=polygon,
            boundary=[Point(x, y) for x, y in polygon.exterior.coords],
        )
    
    def _labeling(self, points: List[Point]):
        X = np.array([[p.x, p.y] for p in points], dtype=np.float32)
        clustering = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size, min_samples=self.min_samples, metric="euclidean")
        labels = clustering.fit_predict(X)
        unique_labels = np.unique(labels)
        return labels, unique_labels


    def _fit_points(self, points: List[Point], zone_type: ZoneType) -> List[Cluster]:
        """Run HDBSCAN on a list of points and return Cluster objects."""

        if len(points) <= self.min_cluster_size:
            return self._fit_few_points(points, zone_type)

        labels, unique_labels = self._labeling(points)

        clusters = []
        for label in unique_labels:
            if label == -1:
                continue
            source_points = [points[i] for i in range(len(points)) if labels[i] == label]
            cluster = self._build_cluster(source_points, zone_type)
            clusters.append(cluster)

        return clusters


    # ------------------------------------------------------
    # Public API
    # ------------------------------------------------------

    def fit(self) -> ClusterOutpost:
        outpost = ClusterOutpost()

        clustering = outpost.airspace_points

        uav_clusters = self._fit_points(
            clustering.uav_points or [], ZoneType.UAV
        )
        mav_clusters = self._fit_points(
            clustering.mav_points or [], ZoneType.MAV
        )

        with outpost:
            outpost.cluster_parcel.clusters = uav_clusters + mav_clusters

        return outpost

