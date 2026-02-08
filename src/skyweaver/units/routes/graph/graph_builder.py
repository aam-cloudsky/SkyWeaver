from typing import Dict, List, Tuple

import igraph as ig

from skyweaver.units.grid.geometry.basecell import BaseCell

from skyweaver.units.grid.structure.basegrid import BaseGrid
from skyweaver.units.routes.graph.graph_pack import (
    AirspaceGraphPack,
    RoutesGraphPack,
    TerminalsGraphPack,
)
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost


class GraphBuilder:
    """
    Builds graph representations from the current grid and path sets.
    """

    def __init__(self, outpost: RoutesOutpost):
        self.outpost = outpost

    def build_airspace_graph(self) -> AirspaceGraphPack:
        graph, cell_to_vid, vid_to_cell = self._build_graph_from_grid(
            self.outpost.grid_parcel.grid
        )
        return AirspaceGraphPack(
            graph=graph,
            _cell_to_vid=cell_to_vid,
            _vid_to_cell=vid_to_cell,
        )

    def build_routes_graph(self, paths: List[List[BaseCell]]) -> RoutesGraphPack:
        g1 = ig.Graph(directed=False)
        cell_to_vid: Dict[BaseCell, int] = {}
        vid_to_cell: Dict[int, BaseCell] = {}

        terminals = self._collect_terminals(paths)

        def get_vid(cell: BaseCell) -> int:
            return self._ensure_vertex(g1, cell, terminals, cell_to_vid, vid_to_cell)

        for path in paths:
            for a, b in zip(path[:-1], path[1:]):
                va = get_vid(a)
                vb = get_vid(b)
                if not g1.are_connected(va, vb):
                    g1.add_edge(va, vb)

        g1["cell_to_vertex_id"] = cell_to_vid
        g1["vertex_id_to_cell"] = vid_to_cell

        return RoutesGraphPack(
            graph=g1,
            _cell_to_vid=cell_to_vid,
            _vid_to_cell=vid_to_cell,
            paths=paths,
        )

    def build_terminals_graph(
        self,
        paths: List[List[BaseCell]],
    ) -> TerminalsGraphPack:
        g2 = ig.Graph(directed=False)
        cell_to_vid: Dict[BaseCell, int] = {}
        vid_to_cell: Dict[int, BaseCell] = {}

        def get_vid(cell: BaseCell) -> int:
            return self._ensure_terminal_vertex(g2, cell, cell_to_vid, vid_to_cell)

        for path_cells in paths:
            start = path_cells[0]
            end = path_cells[-1]
            g2.add_edge(
                get_vid(start),
                get_vid(end),
                weight=self._compute_cost(path_cells),
                path=path_cells,
            )

        g2["cell_to_vertex_id"] = cell_to_vid
        g2["vertex_id_to_cell"] = vid_to_cell

        return TerminalsGraphPack(
            graph=g2,
            _cell_to_vid=cell_to_vid,
            _vid_to_cell=vid_to_cell,
        )

    def _compute_cost(self, path: List[BaseCell]) -> float:
        if len(path) < 2:
            return 0.0
        total_cost = 0.0
        for a, b in zip(path[:-1], path[1:]):
            edge_cost = 0.5 * (a.cost + b.cost)
            total_cost += edge_cost
        return total_cost

    def _build_graph_from_grid(
        self,
        grid: BaseGrid,
    ) -> tuple[ig.Graph, Dict[BaseCell, int], Dict[int, BaseCell]]:
        graph = ig.Graph(directed=False)

        cell_to_vid: Dict[BaseCell, int] = {}
        vid_to_cell: Dict[int, BaseCell] = {}

        for cell in grid.iter_domain_cells():
            if not cell.available:
                continue
            vid = graph.vcount()
            graph.add_vertex()
            cell_to_vid[cell] = vid
            vid_to_cell[vid] = cell

        edges = []
        weights = []

        for cell, vid in cell_to_vid.items():
            for neighbor in grid.neighbors(cell):
                nvid = cell_to_vid.get(neighbor)
                if nvid is None or nvid <= vid:
                    continue
                edges.append((vid, nvid))
                weights.append(0.5 * (cell.cost + neighbor.cost))

        graph.add_edges(edges)
        graph.es["weight"] = weights

        graph["cell_to_vertex_id"] = cell_to_vid
        graph["vertex_id_to_cell"] = vid_to_cell

        return graph, cell_to_vid, vid_to_cell

    def _collect_terminals(self, paths: List[List[BaseCell]]) -> set[BaseCell]:
        terminals: set[BaseCell] = set()
        for path in paths:
            if path:
                terminals.add(path[0])
                terminals.add(path[-1])
        return terminals

    def _ensure_vertex(
        self,
        graph: ig.Graph,
        cell: BaseCell,
        terminals: set[BaseCell],
        cell_to_vid: Dict[BaseCell, int],
        vid_to_cell: Dict[int, BaseCell],
    ) -> int:
        vid = cell_to_vid.get(cell)
        if vid is not None:
            return vid

        vid = graph.vcount()
        graph.add_vertex(
            cell=cell,
            is_terminal=(cell in terminals),
        )
        cell_to_vid[cell] = vid
        vid_to_cell[vid] = cell
        return vid

    def _ensure_terminal_vertex(
        self,
        graph: ig.Graph,
        cell: BaseCell,
        cell_to_vid: Dict[BaseCell, int],
        vid_to_cell: Dict[int, BaseCell],
    ) -> int:
        vid = cell_to_vid.get(cell)
        if vid is not None:
            return vid

        vid = graph.vcount()
        graph.add_vertex()
        cell_to_vid[cell] = vid
        vid_to_cell[vid] = cell
        return vid
