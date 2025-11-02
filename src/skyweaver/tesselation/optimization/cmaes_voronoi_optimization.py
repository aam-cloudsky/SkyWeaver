from typing import List
import numpy as np
from shapely.geometry import Point
import networkx as nx
import cma

from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell
from skyweaver.tesselation.optimization.base_voronoi_optimization import BaseVoronoiOptimization


class CMAESVoronoiOptimization(BaseVoronoiOptimization):
    """
    Voronoi seed optimization using CMA-ES (Covariance Matrix Adaptation Evolution Strategy).
    """

    def __init__(self, n_seeds: int = 10, sigma0: float = 100.0):
        super().__init__()
        self.n_seeds = n_seeds
        self.sigma0 = sigma0  # initial standard deviation for mutations

    # -------------------------------------------------------------
    # Fitness function
    # -------------------------------------------------------------
    def evaluate_seed_points(self, flat_vector: np.ndarray) -> float:
        """Fitness for CMA-ES — returns a scalar cost (lower is better)."""
        n_points = len(flat_vector) // 2
        points = [Point(flat_vector[2*i], flat_vector[2*i+1])
                  for i in range(n_points)]

        try:
            self.update_seed_points(points)
        except Exception as e:
            # penalize invalid Voronoi
            return 1e6

        graph = self.voronoi_config.adjacency_graph
        cells = self.voronoi_config.voronoi_cells
        return self._objective(graph, cells)

    def _objective(self, graph: nx.Graph, cells: List[VoronoiCell]) -> float:
        """Custom global score — here minimizing total edge length."""
        total_dist = 0.0
        for u, v in graph.edges():
            cu, cv = cells[u].seed_point, cells[v].seed_point
            total_dist += cu.distance(cv)
        return total_dist  # CMA-ES minimizes this

    # -------------------------------------------------------------
    # Main optimization routine
    # -------------------------------------------------------------
    def optimize(self, max_generations):
        (xmin, xmax), (ymin, ymax) = self.voronoi_config.domain
        n_dim = 2 * self.n_seeds

        # Initial guess: uniform random within domain
        x0 = np.random.uniform([xmin, ymin] * self.n_seeds,
                               [xmax, ymax] * self.n_seeds)

        # CMA-ES configuration
        es = cma.CMAEvolutionStrategy(x0, self.sigma0, {
            "bounds": [[xmin, ymin] * self.n_seeds, [xmax, ymax] * self.n_seeds],
            "maxiter": max_generations,
            "verb_disp": 1
        })

        #print(f"[INFO] Starting CMA-ES optimization with {self.n_seeds} seeds.")

        while not es.stop():
            solutions = es.ask()
            fitnesses = [self.evaluate_seed_points(
                np.array(s)) for s in solutions]
            es.tell(solutions, fitnesses)
            es.disp()

        result = es.result
        best_vector = result.xbest

        # Build Voronoi with final configuration
        best_points = [Point(best_vector[2*i], best_vector[2*i+1])
                       for i in range(self.n_seeds)]
        self.update_seed_points(best_points)
        #print("[INFO] CMA-ES optimization complete.")


if __name__ == "__main__":

    import plotly.graph_objects as go
    from skyweaver.tesselation.voronoi.voronoi_configuration import VoronoiConfiguration

    opt = CMAESVoronoiOptimization(n_seeds=10, sigma0=500.0)
    opt.optimize(max_generations=20)

    config = VoronoiConfiguration()  # Initialize VoronoiConfig
    fig = go.Figure()

    rng = np.random.default_rng(42)

    # Voronoi cells
    for i, cell in enumerate(config.voronoi_cells):
        if cell.polygon.is_empty:
            continue
        x, y = map(list, cell.polygon.exterior.xy)  # ← FIXED HERE
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            fill="toself",
            fillcolor=f"rgba({rng.integers(0, 255)}, {rng.integers(0, 255)}, {rng.integers(0, 255)}, 0.3)", 
            line=dict(color="black", width=1),
            name=f"Cell {i}",
            hoverinfo="text",
            text=f"Cell {i}<br>Seed: ({cell.seed_point.x:.1f}, {cell.seed_point.y:.1f})"
        ))


    # Graph edges
    for u, v in config.adjacency_graph.edges():
        c1 = config.voronoi_cells[u].seed_point
        c2 = config.voronoi_cells[v].seed_point
        fig.add_trace(go.Scatter(
            x=[c1.x, c2.x], y=[c1.y, c2.y],
            mode="lines", line=dict(color="gray", width=1),
            hoverinfo="none", showlegend=False
        ))

    # Seed points
    fig.add_trace(go.Scatter(
        x=[cell.seed_point.x for cell in config.voronoi_cells],
        y=[cell.seed_point.y for cell in config.voronoi_cells],
        mode="markers+text",
        marker=dict(color="red", size=8, line=dict(
            color="black", width=1)),
        text=[f"S{i}" for i in range(len(config.voronoi_cells))],
        textposition="top center",
        name="Seeds"
    ))

    (xmin, xmax), (ymin, ymax) = config.domain
    fig.update_layout(
        title="CMA-ES Voronoi Optimization Result",
        xaxis=dict(range=[xmin, xmax], showgrid=True,
                    zeroline=False, scaleanchor="y"),
        yaxis=dict(range=[ymin, ymax], showgrid=True, zeroline=False),
        width=800, height=800,
        template="plotly_white"
    )
    fig.show()
