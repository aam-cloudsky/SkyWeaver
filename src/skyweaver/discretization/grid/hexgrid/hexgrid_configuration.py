# src/skyweaver/tessellation/hexgrid/hexgrid_configuration.py

import networkx as nx
from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.null_grid import NullGrid
from skyweaver.instance_segmentation.geometry.cluster import Cluster

from dataclasses import dataclass, field
from typing import List, Tuple



from skyweaver.core.configuration.base_configuration import BaseConfiguration


@dataclass
class HexGridConfiguration(BaseConfiguration):
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """
    domain: Tuple[Tuple[float, float], Tuple[float, float]] = field(default=((-1000, 1000), (-1000, 1000)))
    clusters: List[Cluster] = field(default_factory=list)
    cell_size: float = field(default=100.0)
    grid: BaseGrid = field(default_factory=NullGrid)




