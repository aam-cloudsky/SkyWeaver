# src/skyweaver/scenarios/components/voronoi/voronoi_configuration.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from shapely import Polygon

from skyweaver.core.states.base_configuration import BaseConfiguration
from skyweaver.scenarios.components.voronoi.voronoi_builder import VoronoiBuilder
from skyweaver.scenarios.components.voronoi.voronoi_cell import VoronoiCell


@dataclass
class VoronoiConfiguration(BaseConfiguration):
    """
    Reactive configuration describing the Voronoi decomposition of the airspace.

    Holds:
        - Voronoi cells (with seed point and validity)
        - Adjacency graph between valid cells
        - Cluster centroids, types, and polygons (for context)
    """

    # --- Cluster geometry ---
    # VOU REMOVER ESSAS VARIÁVEIS E DEIXAR COMENTE A CLASSE CLUSTER.
    centroids: Dict[str, Point] = field(default_factory=dict)
    boundaries: Dict[str, List[Point]] = field(default_factory=dict)
    polygons: Dict[str, Polygon] = field(default_factory=dict)
    types: Dict[str, str] = field(default_factory=dict)

    # --- Voronoi decomposition ---
    voronoi_cells: Dict[str, VoronoiCell] = field(
        default_factory=dict)  # {"cell_0": VoronoiCell(...), ...}
    seed_points: List[Point] = field(default_factory=list)

    # --- Graph topology ---
    adjacency_graph: Dict[str, List[str]] = field(default_factory=dict)
    validity_map: Dict[Tuple[str, str], bool] = field(default_factory=dict)

    # --- Metadata ---
    domain: Tuple[Tuple[float, float], Tuple[float, float]] = (
        (-1000, 1000), (-1000, 1000))
    step: int = 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)
        # automatic recomputation at context exit
        if exc_type is None:
            self._build_voronoi_state()

    # ---------------------------------------------------
    # Reactive computation chain
    # ---------------------------------------------------
    def _build_voronoi_state(self):
        """Compute Voronoi cells, validity and adjacency graph."""
        if not self.seed_points:
            return

        # 1. Build Voronoi cells (placeholder, using VoronoiBuilder)
        builder = VoronoiBuilder()
        cells = builder.build(self.seed_points)

        # 2. Update local state
        self.voronoi_cells = {cell.id: cell for cell in cells}

        # 3. Rebuild adjacency and validity maps
        self.build_validity_map()
        self.build_adjacency_graph()
        
