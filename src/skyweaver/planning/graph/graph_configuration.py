# src/skyweaver/core/configuration/cluster_configuration.py
from dataclasses import dataclass, field
from typing import List
from shapely import Point
from skyweaver.core.configuration.base_configuration import BaseConfiguration
from skyweaver.core.enums.zone_type import ZoneType
from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.null_grid import NullGrid
from skyweaver.instance_segmentation.geometry.cluster import Cluster


@dataclass
class GraphConfiguration(BaseConfiguration):
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


    # === Cluster composition ===
    clusters: list[Cluster] = field(default_factory=list)
    grid: BaseGrid = field(default_factory=NullGrid)
