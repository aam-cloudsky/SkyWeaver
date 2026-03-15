from typing import Dict, List, Tuple

import igraph as ig

from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.routes.graph.graph_pack import (
    AirspaceGraphPack,
    RoutesGraphPack,
    TerminalsGraphPack,
)
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost


# TODO: Refactor the GraphBuilder to avoid code duplication and improve maintainability.
# The current implementation has several similar patterns that can be abstracted into helper
# methods or a more generic graph construction approach.
class GraphBuilder:
    """
    Builds graph representations from the current grid and path sets.
    Topology only. Weight computation should not live here.
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

    def build_routes_graph(self, paths: List[List[HexCell]]) -> RoutesGraphPack:
        g1 = ig.Graph(directed=False)
        cell_to_vid: Dict[HexCell, int] = {}
        vid_to_cell: Dict[int, HexCell] = {}

        terminals = self._collect_terminals(paths)

        def get_vid(cell: HexCell) -> int:
            return self._ensure_vertex(g1, cell, terminals, cell_to_vid, vid_to_cell)

        edges = set()
        for path in paths:
            for a, b in zip(path[:-1], path[1:]):
                va = get_vid(a)
                vb = get_vid(b)

                edge = tuple(sorted((va, vb)))
                edges.add(edge)
        # if not g1.are_connected(va, vb):
        #    g1.add_edge(va, vb)

        g1.add_edges(list(edges))
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
        paths: List[List[HexCell]],
    ) -> TerminalsGraphPack:
        g2 = ig.Graph(directed=False)
        cell_to_vid: Dict[HexCell, int] = {}
        vid_to_cell: Dict[int, HexCell] = {}

        def get_vid(cell: HexCell) -> int:
            return self._ensure_terminal_vertex(g2, cell, cell_to_vid, vid_to_cell)

        for path_cells in paths:
            start = path_cells[0]
            end = path_cells[-1]
            g2.add_edge(
                get_vid(start),
                get_vid(end),
                path=path_cells,
            )

        # TODO: Redundância no armazenamento de mapas, pode ser otimizado ?
        g2["cell_to_vertex_id"] = cell_to_vid
        g2["vertex_id_to_cell"] = vid_to_cell

        return TerminalsGraphPack(
            graph=g2,
            _cell_to_vid=cell_to_vid,
            _vid_to_cell=vid_to_cell,
        )

    def _build_graph_from_grid(
        self,
        grid: HexGrid,
    ) -> tuple[ig.Graph, Dict[HexCell, int], Dict[int, HexCell]]:
        graph = ig.Graph(directed=False)

        cell_to_vid: Dict[HexCell, int] = {}
        vid_to_cell: Dict[int, HexCell] = {}

        for cell in grid.iter_domain_cells():
            if not cell.is_traversable:
                continue
            vid = graph.vcount()
            graph.add_vertex()
            cell_to_vid[cell] = vid
            vid_to_cell[vid] = cell

        edges = []

        for cell, vid in cell_to_vid.items():
            for neighbor in grid.neighbors(cell):
                nvid = cell_to_vid.get(neighbor)
                if nvid is None or nvid <= vid:
                    continue
                edges.append((vid, nvid))

        graph.add_edges(edges)

        # TODO: Esses cálculos estão bem parecidos com o
        # build terminal paths, pode ser otimizado para evitar redundância
        graph["cell_to_vertex_id"] = cell_to_vid
        graph["vertex_id_to_cell"] = vid_to_cell

        return graph, cell_to_vid, vid_to_cell

    def _collect_terminals(self, paths: List[List[HexCell]]) -> set[HexCell]:
        terminals: set[HexCell] = set()
        for path in paths:
            if path:
                terminals.add(path[0])
                terminals.add(path[-1])
        return terminals

    def _ensure_vertex(
        self,
        graph: ig.Graph,
        cell: HexCell,
        terminals: set[HexCell],
        cell_to_vid: Dict[HexCell, int],
        vid_to_cell: Dict[int, HexCell],
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
        cell: HexCell,
        cell_to_vid: Dict[HexCell, int],
        vid_to_cell: Dict[int, HexCell],
    ) -> int:
        vid = cell_to_vid.get(cell)
        if vid is not None:
            return vid

        vid = graph.vcount()
        graph.add_vertex()

        # TODO: Tá parecendo muito similar com os outros
        # códigos. Realmente preciso refatorar.
        cell_to_vid[cell] = vid
        vid_to_cell[vid] = cell
        return vid
