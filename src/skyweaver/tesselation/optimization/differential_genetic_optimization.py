from typing import List
import numpy as np
from shapely.geometry import Point
from scipy.optimize import differential_evolution
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell
from skyweaver.tesselation.optimization.base_voronoi_optimization import BaseVoronoiOptimization
import networkx as nx


class DifferentialGeneticVoronoiOptimization(BaseVoronoiOptimization):
    """
    Genetic optimization of Voronoi seed points using differential evolution.
    """

    # TODO:
    # [] Validity cell checks -> MAV > threshold should not be considered valid to connect
    # [] Multi-criteria scoring (overlap, distance, entropy, etc.)

    def __init__(self, n_seeds: int = 10):
        super().__init__()
        self.n_seeds = n_seeds  # number of seed points to optimize

    # --------------------------------------------------------------
    # Scoring utilities
    # --------------------------------------------------------------
    def _sum_all_distances(self, valid_graph: nx.Graph, cells: List[VoronoiCell]) -> float:
        """Calculate the sum of Euclidean distances between all connected valid Voronoi cells."""
        total_distance = 0.0
        for u, v in valid_graph.edges():
            cell_u: VoronoiCell = cells[u]
            cell_v: VoronoiCell = cells[v]
            total_distance += cell_u.seed_point.distance(cell_v.seed_point)
        return total_distance

    def compute_global_score(self, graph, cells) -> float:
        """Compute global Voronoi quality score (lower distance → higher score)."""
        return 1.0 / (self._sum_all_distances(graph, cells) + 1e-6)

    # --------------------------------------------------------------
    # Fitness function
    # --------------------------------------------------------------
    def evaluate_seed_points(self, flat_vector):
        """Fitness function for differential evolution — robust to invalid seeds."""
        try:
            n_points = len(flat_vector) // 2
            if n_points < 2:
                print("[WARN] Not enough points to build Voronoi (need ≥2).")
                return 1e6  # Penalize invalid configurations

            points = [Point(flat_vector[2 * i], flat_vector[2 * i + 1])
                      for i in range(n_points)]

            try:
                self.update_seed_points(points)
            except ValueError as e:
                print(f"[WARN] Skipping invalid Voronoi: {e}")
                return 1e6

            score = self.compute_global_score(
                self.voronoi_config.adjacency_graph,
                self.voronoi_config.voronoi_cells,
            )

            return -float(score)  # minimize negative score
        except Exception as e:
            print(
                f"[FATAL] Exception during fitness eval: {type(e).__name__}: {e}")
            return 1e6

    # --------------------------------------------------------------
    # Main optimization routine
    # --------------------------------------------------------------
    def optimize(self, max_generations: int = 100):
        """Run differential evolution to optimize Voronoi seed positions."""
        (xmin, xmax), (ymin, ymax) = self.voronoi_config.domain

        # Create bounds for each seed point
        bounds = [(xmin, xmax), (ymin, ymax)] * self.n_seeds

        print(f"[INFO] Starting optimization with {self.n_seeds} seeds "
              f"and {len(bounds)} variables.")

        # CMA-ES ou Bayesian Optimization (TPE) could be alternatives
        # evolutive strategy
        result = differential_evolution( 
            func=self.evaluate_seed_points,
            bounds=bounds,
            maxiter=max_generations,
            strategy="best1bin",
            popsize=15,
            mutation=(0.5, 1),
            recombination=0.7,
            disp=True,
            polish=True,
        )

        optimized_vector = result.x
        n_points = len(optimized_vector) // 2
        optimized_points = [Point(optimized_vector[2 * i], optimized_vector[2 * i + 1])
                            for i in range(n_points)]

        print(
            f"[INFO] Optimization finished. Building Voronoi with {n_points} points.")
        self.update_seed_points(optimized_points)


# ==========================================================
# Stand-alone demo
# ==========================================================
# ==========================================================
# Stand-alone demo
# ==========================================================
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from shapely.geometry import Point, LineString

    print("[INFO] Testing GeneticVoronoiOptimization...")

    # Reproducibility
    np.random.seed(42)

    # 1️⃣ Instantiate optimizer
    optimizer = DifferentialGeneticVoronoiOptimization(n_seeds=40)

    # 2️⃣ Run optimization
    optimizer.optimize(max_generations=5)

    # 3️⃣ Retrieve Voronoi configuration (built internally)
    config = optimizer.voronoi_config

    # 4️⃣ Plot Voronoi cells and adjacency graph
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_title("Genetic Voronoi Optimization — Voronoi Diagram and Graph")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")

    # --- Draw Voronoi cells
    for cell in config.voronoi_cells:
        if cell.polygon is not None:
            x, y = cell.polygon.exterior.xy
            ax.plot(x, y, color="gray", linewidth=0.8)
            ax.fill(x, y, color="lightgray", alpha=0.2)

    # --- Draw adjacency graph (edges between cell centroids)
    for u, v in config.adjacency_graph.edges():
        c1 = config.voronoi_cells[u].seed_point
        c2 = config.voronoi_cells[v].seed_point
        line = LineString([(c1.x, c1.y), (c2.x, c2.y)])
        x, y = line.xy
        ax.plot(x, y, color="black", linewidth=0.8, alpha=0.5)

    # --- Draw seed points
    xs = [cell.seed_point.x for cell in config.voronoi_cells]
    ys = [cell.seed_point.y for cell in config.voronoi_cells]
    ax.scatter(xs, ys, color="royalblue", s=60, label="Seed Points")

    (xmin, xmax), (ymin, ymax) = config.domain
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()

    print("[INFO] GeneticVoronoiOptimization test complete.")
