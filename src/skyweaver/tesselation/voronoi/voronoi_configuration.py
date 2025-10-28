# src/skyweaver/scenarios/components/voronoi/voronoi_configuration.py
from dataclasses import dataclass, field
from typing import List

import numpy as np
from shapely import Point

from skyweaver.core.configuration.base_configuration import BaseConfiguration
from skyweaver.instance_segmentation.geometry.cluster import Cluster
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell

from scipy.spatial import Voronoi
import networkx as nx
@dataclass
class VoronoiConfiguration(BaseConfiguration):
    """
    Reactive configuration describing the Voronoi decomposition of the airspace.

    Holds:
        - Voronoi cells (with seed point, polygon, and validity)
        - Adjacency graph between valid cells
        - Reference to cluster geometry (for contextual restrictions)
    """

    # --- Context: high-level spatial structure ---
    clusters: list[Cluster] = field(default_factory=list)

    # --- Voronoi decomposition ---
    seed_points: list[Point] = field(default_factory=list)
    voronoi_cells: list[VoronoiCell] = field(default_factory=list)

    # --- Graph topology ---
    adjacency_graph: nx.Graph = field(default_factory=nx.Graph)
    voronoi_diagram: Voronoi = field(default_factory=lambda: Voronoi(np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0],
    ])))

    score: float = field(default=0.0)

    # --- Metadata ---
    domain: tuple[tuple[float, float], tuple[float, float]] = ((-1000, 1000), (-1000, 1000))
    step: int = 0

   