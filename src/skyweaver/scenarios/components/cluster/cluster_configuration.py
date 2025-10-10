# src/skyweaver/core/configuration/cluster_configuration.py
from dataclasses import dataclass, field
from typing import List, Dict
from skyweaver.core.geometry.point import Point
from skyweaver.core.states.air_space_state import AirspaceState
from skyweaver.core.states.base_configuration import BaseConfiguration


@dataclass
class ClusterConfiguration(BaseConfiguration):
    """Immutable snapshot view of AirspaceState for clustering."""
    # Cluster-level information
    centroids: List[Point] = field(default_factory=list)
    cluster_polygons: Dict[str, List[Point]] = field(default_factory=dict)
    uav_points: List[Point] = field(default_factory=list)
    mav_points: List[Point] = field(default_factory=list)

