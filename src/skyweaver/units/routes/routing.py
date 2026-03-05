import math
from typing import Iterable, List

from typing import Dict, List
import igraph as ig

from skyweaver.core.logistics.depot import Depot
from itertools import combinations


from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.routes.graph.graph_pack import AirspaceGraphPack


class Routing:

    # def __init__(self, airspace_graph: AirspaceGraphPack):
    # self.graph = airspace_graph.graph
    # self.cell_to_vid: Dict[HexCell, int] = airspace_graph._cell_to_vid
    # self.vid_to_cell: Dict[int, HexCell] = airspace_graph._vid_to_cell
    STEP_WEIGHT = 1

    @staticmethod
    def obtain_edges_weights(airspace_graph: AirspaceGraphPack):
        weights: list[float] = []

        for edge in airspace_graph.graph.es:
            u, v = edge.tuple
            cell_u = airspace_graph._vid_to_cell[u]
            cell_v = airspace_graph._vid_to_cell[v]
            edge_weight = Routing.STEP_WEIGHT + (0.5 * (cell_u.cost + cell_v.cost))
            weights.append(edge_weight)

        return weights

    @staticmethod
    def shortest_path(
        airspace_graph: AirspaceGraphPack,
        a: HexCell,
        b: HexCell,
    ) -> tuple[float, list[HexCell] | None]:
        """
        Shortest path query on base graph (G0).

        Returns:
            (cost, path_cells or None)
        """

        v_a = airspace_graph._cell_to_vid[a]
        v_b = airspace_graph._cell_to_vid[b]

        weights: list[float] = Routing.obtain_edges_weights(airspace_graph)

        res = airspace_graph.graph.get_shortest_paths(
            v=v_a,
            to=v_b,
            weights=weights,
            output="vpath",
        )

        if not res or not res[0]:
            return float("inf"), None

        vpath = res[0]
        cells = [airspace_graph._vid_to_cell[v] for v in vpath]

        cost = 0.0
        for u, v in zip(vpath[:-1], vpath[1:]):
            eid = airspace_graph.graph.get_eid(u, v)
            cost += airspace_graph.graph.es[eid]["weight"]

        return cost, cells

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

        for a, b in combinations(terminals, 2):
            if (
                a not in airspace_graph._cell_to_vid
                or b not in airspace_graph._cell_to_vid
            ):
                continue

            cost, cells = Routing.shortest_path(airspace_graph, a, b)

            # to make sure invalid path will not to propagate
            if cells is not None and not math.isinf(cost):
                paths.append(cells)

        return paths
