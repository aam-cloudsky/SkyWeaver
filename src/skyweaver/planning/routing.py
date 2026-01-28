
from typing import Iterable, List

from typing import Dict, List
import igraph as ig

from skyweaver.core.logistics.depot import Depot
from skyweaver.grid.geometry.basecell import BaseCell
from itertools import combinations


class Routing:


    def __init__(self, graph: ig.Graph):
        self.graph = graph
        self.cell_to_vid: Dict[BaseCell, int] = graph["cell_to_vertex_id"]
        self.vid_to_cell: Dict[int, BaseCell] = graph["vertex_id_to_cell"]

    def shortest_path(
        self,
        a: BaseCell,
        b: BaseCell,
        return_path: bool = True,
    ) -> tuple[float, list[BaseCell] | None]:
        """
        Shortest path query on base graph (G0).

        Returns:
            (cost, path_cells or None)
        """

        v_a = self.cell_to_vid[a]
        v_b = self.cell_to_vid[b]

        res = self.graph.get_shortest_paths(
            v=v_a,
            to=v_b,
            weights="weight",
            output="vpath" if return_path else "epath",
        )

        if not res or not res[0]:
            return float("inf"), None

        if not return_path:
            cost = sum(self.graph.es[eid]["weight"] for eid in res[0])
            return cost, None

        vpath = res[0]
        cells = [self.vid_to_cell[v] for v in vpath]

        cost = 0.0
        for u, v in zip(vpath[:-1], vpath[1:]):
            eid = self.graph.get_eid(u, v)
            cost += self.graph.es[eid]["weight"]

        return cost, cells




def compute_terminal_paths(
    planner: Routing,
    terminals: Iterable[BaseCell],
) -> List[List[BaseCell]]:
    """
    Compute shortest paths between all terminal pairs (G0 → paths).

    Returns:
        List of paths (each path is a list of BaseCell)
    """
    paths: List[List[BaseCell]] = []

    for a, b in combinations(terminals, 2):
        if a not in planner.cell_to_vid or b not in planner.cell_to_vid:
            continue

        cost, cells = planner.shortest_path(a, b)
        if cells is not None:
            paths.append(cells)

    return paths