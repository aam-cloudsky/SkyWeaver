# src/skyweaver/tessellation/hexgrid/hexgrid_configuration.py

import networkx as nx
from skyweaver.instance_segmentation.geometry.cluster import Cluster
from skyweaver.discretization.hexgrid.hexcell import HexCell

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
    hex_cells: List[HexCell] = field(default_factory=list)
    adjacency_graph: nx.Graph = field(default_factory=nx.Graph)
    clusters: List[Cluster] = field(default_factory=list)
    cell_size: float = field(default=1.0)





