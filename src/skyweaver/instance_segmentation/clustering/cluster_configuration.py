# src/skyweaver/core/configuration/cluster_configuration.py
from dataclasses import dataclass, field
from typing import List
from shapely import Point
from skyweaver.core.configuration.base_configuration import BaseConfiguration
from skyweaver.core.enums.zone_type import ZoneType
from skyweaver.instance_segmentation.geometry.cluster import Cluster


@dataclass
class ClusterConfiguration(BaseConfiguration):
    """
    Declarative structural view of the clustering state within the AirspaceState.

    Each cluster is represented by:
        - a unique ID (e.g., 'UAV_0', 'MAV_1')
        - a set of member points
        - a centroid
        - a boundary (list of perimeter points)
        - a polygon (solid geometric region)
        - a type label ('UAV' or 'MAV')
    """

    # === Inputs ===
    uav_points: List[Point] = field(default_factory=list)
    mav_points: List[Point] = field(default_factory=list)

    # === Cluster composition ===
    clusters: list[Cluster] = field(default_factory=list)

    # ----------------------------------------------------------
    # --- Utility methods ---
    # ----------------------------------------------------------
    def get_by_type(self, zone_type: ZoneType) -> List[Cluster]:
        """Return all clusters that match the given zone type."""
        return [c for c in self.clusters if c.zone_type == zone_type]
    
    def summary(self) -> str:
        """Provide a compact human-readable summary for debugging."""
        n_uav = len(self.get_by_type(ZoneType.UAV))
        n_mav = len(self.get_by_type(ZoneType.MAV))
        return f"ClusterConfiguration: {n_uav} UAV clusters, {n_mav} MAV clusters"
