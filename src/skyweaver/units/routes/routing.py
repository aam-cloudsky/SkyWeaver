import math
from typing import Iterable, List

from typing import Dict, List
import igraph as ig

from skyweaver.core.logistics.depot import Depot
from itertools import combinations


from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.routes.graph.graph_pack import AirspaceGraphPack

# ---------------------------------------------------------------------
# NOTE: Incremental path recomputation (future optimization)
#
# Currently, whenever cell weights change (e.g., restrictions added or
# removed), terminal paths are recomputed from scratch.
#
# In principle this could be optimized:
#
# 1. Cost increases (e.g., adding restrictions)
#    Only paths that traverse the affected cells must be recomputed.
#    This could be implemented by maintaining an index:
#
#        cell -> paths using that cell
#
#    Then only those paths would be recomputed.
#
# 2. Cost decreases (e.g., removing restrictions)
#    This case is more complex. A new shorter route could appear that
#    does not intersect any previously optimal path. In this case many
#    paths may need recomputation.
#
# Properly handling both cases leads to dynamic shortest-path algorithms
# such as LPA* or D*, which is beyond the current scope of the system.
#
# In the current system the number of terminals is small, so full
# recomputation remains computationally acceptable while keeping the
# implementation simple.
#
# Future optimization ideas:

# TODO: Recompute only paths affected by weight increases.
# TODO: Recompute all paths when weight decreases occur.
# TODO: Maintain a cell -> paths index to detect paths affected by weight increases.
# TODO: When weights decrease, recompute all terminal paths to ensure optimality.
# ---------------------------------------------------------------------
# 2. Terminal connectivity optimization
#
# Currently, routes are computed between all pairs of n terminals:
#
#        O(n^2) shortest-path queries.
#
# This becomes expensive as the number of terminals grows.
#
# A possible simplification is to connect each terminal only to its
# nearest neighbors instead of computing all-to-all paths.
#
# For example:
#
#        terminal -> k nearest terminals
#
# where k is a small constant (e.g., 2–3).
#
# This reduces the number of routing queries from:
#
#        O(n^2)
#
# to approximately:
#
#        O(kn)
#
# while still producing a well-connected routes graph in most cases.
#
#
# This optimization is not implemented yet because the number of
# terminals in the current system is small and the full all-pairs
# computation remains manageable.
#
# TODO: Consider replacing all-pairs routing with k-nearest terminal
#       connectivity when the number of terminals grows.
# TODO: Add the k parameter inside the yaml file.
# ---------------------------------------------------------------------


class Routing:

    # def __init__(self, airspace_graph: AirspaceGraphPack):
    # self.graph = airspace_graph.graph
    # self.cell_to_vid: Dict[HexCell, int] = airspace_graph._cell_to_vid
    # self.vid_to_cell: Dict[int, HexCell] = airspace_graph._vid_to_cell
    STEP_WEIGHT = 1

    @staticmethod
    def edge_weight(a: HexCell, b: HexCell) -> float:
        return Routing.STEP_WEIGHT + 0.5 * (a.cost + b.cost)

    @staticmethod
    def path_weight(path: List[HexCell]) -> float:
        total = 0.0
        for a, b in zip(path[:-1], path[1:]):
            total += Routing.edge_weight(a, b)
        return total

    @staticmethod
    def obtain_edges_weights(airspace_graph: AirspaceGraphPack):
        weights: list[float] = []

        for edge in airspace_graph.graph.es:
            u, v = edge.tuple
            cell_u = airspace_graph._vid_to_cell[u]
            cell_v = airspace_graph._vid_to_cell[v]
            edge_weight = Routing.edge_weight(cell_u, cell_v)
            weights.append(edge_weight)

        return weights

    @staticmethod
    def shortest_path(
        airspace_graph: AirspaceGraphPack,
        a: HexCell,
        b: HexCell,
        weights: list[float],
    ) -> tuple[float, list[HexCell] | None]:
        """
        Shortest path query on base graph (G0).

        Returns:
            (cost, path_cells or None)
        """

        v_a = airspace_graph._cell_to_vid[a]
        v_b = airspace_graph._cell_to_vid[b]

        # weights: list[float] = Routing.obtain_edges_weights(airspace_graph)

        res = airspace_graph.graph.get_shortest_paths(
            v=v_a,
            to=v_b,
            weights=weights,
            output="vpath",
        )

        if not res or not res[0]:
            return float("inf"), None

        vpath = res[0]
        path: list[HexCell] = [airspace_graph._vid_to_cell[v] for v in vpath]

        path_weight = Routing.path_weight(path)
        return path_weight, path

    @staticmethod
    def compute_terminal_paths(
        airspace_graph: AirspaceGraphPack,
        terminals: Iterable[HexCell],
    ) -> List[List[HexCell]]:
        """
        Compute shortest paths between all terminal (AirspaceGraphPack G0 → paths).

        Returns:
            List of paths (each path is a list of HexCell)
        """
        paths: List[List[HexCell]] = []
        weights: list[float] = Routing.obtain_edges_weights(airspace_graph)
        for a, b in combinations(terminals, 2):
            if (
                a not in airspace_graph._cell_to_vid
                or b not in airspace_graph._cell_to_vid
            ):
                continue

            cost, cells = Routing.shortest_path(airspace_graph, a, b, weights)

            # to make sure invalid path will not to propagate
            if cells is not None and not math.isinf(cost):
                paths.append(cells)

        return paths
