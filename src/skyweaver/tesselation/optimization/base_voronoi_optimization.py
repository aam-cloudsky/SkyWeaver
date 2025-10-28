from typing import Dict, List
from skyweaver.tesselation.voronoi.voronoi_builder import VoronoiBuilder
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell

from scipy.spatial import Voronoi
import networkx as nx

from skyweaver.tesselation.voronoi.voronoi_configuration import VoronoiConfiguration

class BaseVoronoiOptimization:
    def __init__(self):
        self.voronoi_config = VoronoiConfiguration()

    def update_seed_points(self, seed_points: List):
        """Update the seed points and rebuild the Voronoi state."""
        
        domain = self.voronoi_config.domain
        cells, graph, vor = self._build_voronoi(seed_points, domain)
        self._update_cluster_cells_overlap(cells)
        
        with self.voronoi_config:
            self.voronoi_config.seed_points = seed_points
            self.voronoi_config.voronoi_cells = cells
            self.voronoi_config.adjacency_graph = graph
            self.voronoi_config.voronoi_diagram = vor


    def _build_voronoi(self, seed_points: List, domain: tuple) -> tuple[List[VoronoiCell], nx.Graph, Voronoi]:
        """Compute Voronoi cells, validity, and adjacency graph."""

        builder = VoronoiBuilder()
        cells, graph, vor = builder.build(domain, seed_points=seed_points)

        return cells, graph, vor

    def _update_cluster_cells_overlap(self, cells: List[VoronoiCell]):
        """Update overlap of Voronoi cells based on cluster overlaps."""

        for cell in cells:
            cell.update_overlap(self.voronoi_config.clusters)