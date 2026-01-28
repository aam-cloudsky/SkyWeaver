
from typing import AbstractSet, Dict, List, Tuple



from skyweaver.planning.logistics.planning_outpost import PlanningOutpost
import igraph as ig

from skyweaver.grid.geometry.basecell import BaseCell
from skyweaver.grid.structure.basegrid import BaseGrid

class GraphBuilder:
    """
    Builds an explicit graph representation from the current AirspaceState
    and synchronizes it via GraphOutpost.
    """

    def __init__(self, outpost: PlanningOutpost):
        # Configuration is an access façade, not an external dependency
        self.outpost: PlanningOutpost = outpost

    def build_navigation_graph(self) -> ig.Graph:
        """
        Build navigation graph (G3) from current grid in outpost.
        """
        return self._build_graph_from_grid(self.outpost.grid_parcel.grid)

    def _build_graph_from_grid(self, grid: BaseGrid) -> ig.Graph:

        graph = ig.Graph(directed=False)

        # ---------------------------------------------
        # 1. Map BaseCell -> vertex id
        # ---------------------------------------------
        cell_to_vertex_id: Dict[BaseCell, int] = {}
        vertex_id_to_cell: Dict[int, BaseCell] = {}

        # Pega todas as células navegáveis e cria um vértice para cada uma
        for cell in grid.iter_domain_cells():
            if not cell.available:
                continue

            vertex_id = graph.vcount()
            graph.add_vertex()

            cell_to_vertex_id[cell] = vertex_id
            vertex_id_to_cell[vertex_id] = cell

        # ---------------------------------------------
        # 2. Create edges (avoid duplicates)
        # ---------------------------------------------
        edges = []
        weights = []

        for cell, vertex_id in cell_to_vertex_id.items():
            for neighbor in grid.neighbors(cell):
                if neighbor not in cell_to_vertex_id:
                    continue

                neighbor_vertex_id = cell_to_vertex_id[neighbor]
                # Avoid duplicating undirected edges
                if neighbor_vertex_id <= vertex_id:
                    continue

                edges.append((vertex_id, neighbor_vertex_id))

                # Edge cost is average of cell costs
                edge_cost = 0.5 * (cell.cost + neighbor.cost)
                weights.append(edge_cost)

        graph.add_edges(edges)
        graph.es["weight"] = weights

        # ---------------------------------------------
        # 3. Store mapping in graph attributes
        # ---------------------------------------------
        graph["cell_to_vertex_id"] = cell_to_vertex_id
        graph["vertex_id_to_cell"] = vertex_id_to_cell

        return graph
    
    def build_terminal_graph(
        self,
        paths: List[Tuple[List[BaseCell], float]]
    ) -> ig.Graph:
        """
        Build terminal graph (G2) from path results.

        Vertices:
            unique path endpoints

        Edges:
            one per path, carrying full path and cost
        """

        g2 = ig.Graph(directed=False)

        cell_to_vid: Dict[BaseCell, int] = {}
        vid_to_cell: Dict[int, BaseCell] = {}

        def get_vid(cell: BaseCell) -> int:
            if cell not in cell_to_vid:
                vid = g2.vcount()
                g2.add_vertex()
                cell_to_vid[cell] = vid
                vid_to_cell[vid] = cell
            return cell_to_vid[cell]

        # --------------------------------------------------
        # Build graph from paths
        # --------------------------------------------------
        for path_cells, cost in paths:

            start = path_cells[0]
            end = path_cells[-1]

            v_start = get_vid(start)
            v_end = get_vid(end)

            g2.add_edge(
                v_start,
                v_end,
                weight=cost,
                path=path_cells,
            )

        g2["cell_to_vertex_id"] = cell_to_vid
        g2["vertex_id_to_cell"] = vid_to_cell

        return g2
    
    def build_path_induced_graph(
        self,
        paths: List[List[BaseCell]],
    ) -> ig.Graph:
        """
        Build a graph induced (G1) by the given paths.

        - Each vertex represents a BaseCell appearing in any path
        - Each edge represents adjacency along a path
        - Vertex attribute:
            - cell: BaseCell
            - is_terminal: bool (True if cell is start or end of any path)
        """

        g1 = ig.Graph(directed=False)

        cell_to_vid: Dict[BaseCell, int] = {}
        vid_to_cell: Dict[int, BaseCell] = {}

        terminals: set[BaseCell] = set()

        # --------------------------------------------------
        # 1. Identify terminals
        # --------------------------------------------------
        for path in paths:
            if not path:
                continue
            terminals.add(path[0])
            terminals.add(path[-1])

        # --------------------------------------------------
        # 2. Vertex creation helper
        # --------------------------------------------------
        def get_vid(cell: BaseCell) -> int:
            if cell not in cell_to_vid:
                vid = g1.vcount()
                g1.add_vertex(
                    cell=cell,
                    is_terminal=(cell in terminals),
                )
                cell_to_vid[cell] = vid
                vid_to_cell[vid] = cell
            return cell_to_vid[cell]

        # --------------------------------------------------
        # 3. Add edges from paths
        # --------------------------------------------------
        for path in paths:
            for a, b in zip(path[:-1], path[1:]):
                va = get_vid(a)
                vb = get_vid(b)

                if not g1.are_connected(va, vb):
                    g1.add_edge(va, vb)

        # --------------------------------------------------
        # 4. Store mappings
        # --------------------------------------------------
        g1["cell_to_vertex_id"] = cell_to_vid
        g1["vertex_id_to_cell"] = vid_to_cell

        return g1

