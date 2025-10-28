from typing import List
import numpy as np
from shapely.geometry import Point
from scipy.optimize import differential_evolution
from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell
from skyweaver.tesselation.optimization.base_voronoi_optimization import BaseVoronoiOptimization
import networkx as nx


class GeneticVoronoiOptimization(BaseVoronoiOptimization):
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
