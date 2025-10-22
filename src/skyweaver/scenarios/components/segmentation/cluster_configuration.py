# src/skyweaver/core/configuration/cluster_configuration.py
from dataclasses import dataclass, field
from typing import Dict, List
from shapely.geometry import Polygon
from skyweaver.core.geometry.point import Point
from skyweaver.core.states.base_configuration import BaseConfiguration


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
    clusters: Dict[str, List[Point]] = field(default_factory=dict) # {"UAV_0": [Point(...), ...], "MAV_1": [Point(...), ...]}

    # === Cluster attributes ===
    centroids: Dict[str, Point] = field(default_factory=dict)
    boundaries: Dict[str, List[Point]] = field(default_factory=dict)
    polygons: Dict[str, Polygon] = field(default_factory=dict) # {"UAV_0": Polygon(...), ...}
    types: Dict[str, str] = field(default_factory=dict)
