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
        
        #print("[DEBUG] Updated Voronoi configuration:",len(self.voronoi_config.clusters))
        
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


    def optimize(self, max_generations: int):
        """Placeholder for optimization routine to be implemented in subclasses."""
        raise NotImplementedError(
            "Optimize method must be implemented in subclasses."
        )


# ==========================================================
# Stand-alone test for BaseVoronoiOptimization
# ==========================================================
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from shapely.geometry import Point, LineString
    import numpy as np

    print("[INFO] Testing BaseVoronoiOptimization...")

    # Reproducibility
    np.random.seed(42)

    # 1️⃣ Instantiate optimizer (uses default domain from VoronoiConfiguration)
    base_opt = BaseVoronoiOptimization()

    # 2️⃣ Generate random seed points
    n_points = 20
    (xmin, xmax), (ymin, ymax) = base_opt.voronoi_config.domain
    seed_points = [Point(*np.random.uniform([xmin, ymin], [xmax, ymax]))
                   for _ in range(n_points)]

    # 3️⃣ Update Voronoi state
    base_opt.update_seed_points(seed_points)
    config = base_opt.voronoi_config

    # 4️⃣ Plot Voronoi cells and adjacency graph
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_title("BaseVoronoiOptimization — Full Bounded Voronoi Diagram")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    # --- Draw Voronoi cells
    for cell in config.voronoi_cells:
        if cell.polygon is not None:
            poly = cell.polygon.buffer(0)
            if not poly.is_empty:
                x, y = poly.exterior.xy
                ax.fill(x, y, color="lightgray", alpha=0.3,
                        edgecolor="black", linewidth=0.8)

    # --- Draw adjacency graph (edges between cell centroids)
    for u, v in config.adjacency_graph.edges():
        c1 = config.voronoi_cells[u].seed_point
        c2 = config.voronoi_cells[v].seed_point
        line = LineString([(c1.x, c1.y), (c2.x, c2.y)])
        x, y = line.xy
        ax.plot(x, y, color="gray", linewidth=0.8, alpha=0.5)

    # --- Draw seed points
    xs = [cell.seed_point.x for cell in config.voronoi_cells]
    ys = [cell.seed_point.y for cell in config.voronoi_cells]
    ax.scatter(xs, ys, color="royalblue", s=60, label="Seed Points")

    # --- Draw domain boundary
    ax.plot(
        [xmin, xmax, xmax, xmin, xmin],
        [ymin, ymin, ymax, ymax, ymin],
        color="black", linewidth=1.2, linestyle="--", label="Domain"
    )

    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()

    print("[INFO] BaseVoronoiOptimization test complete.")
