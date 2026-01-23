from abc import abstractmethod
from typing import AbstractSet, Dict, List, Tuple
from skyweaver.discretization.grid.base_cell import BaseCell

from skyweaver.planning.graph.graph_configuration import GraphConfiguration
import igraph as ig
from skyweaver.discretization.grid.base_grid import BaseGrid

class GraphBuilder:
    """
    Builds an explicit graph representation from the current AirspaceState
    and synchronizes it via GraphConfiguration.
    """

    def __init__(self, config: GraphConfiguration):
        # Configuration is an access façade, not an external dependency
        self.config: GraphConfiguration = config

    def build(self) -> ig.Graph:
        return self._build_graph_from_grid(self.config.grid)

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
    
    def build_terminals_graph_from_paths(
        self,
        paths: List[Tuple[List[BaseCell], float]]
    ) -> ig.Graph:
        """
        Build terminal graph (G1) from path results.

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
    
    def build_paths_graph(
        self,
        paths: List[List[BaseCell]],
    ) -> ig.Graph:
        """
        Build a graph induced by the given paths.

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


if __name__ == "__main__":
    import time
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    from skyweaver.discretization.grid.hexgrid.hexgrid import HexGrid

    t0 = time.perf_counter()

    # ---------------------------------------
    # 1. Build grid and graph
    # ---------------------------------------
    t_grid_start = time.perf_counter()
    grid = HexGrid(cell_size=100.0)
    t_grid_end = time.perf_counter()

    config = GraphConfiguration()
    builder = GraphBuilder(config)

    t_graph_start = time.perf_counter()
    graph = builder.build()
    t_graph_end = time.perf_counter()

    num_vertices = graph.vcount()
    num_edges = graph.ecount()

    print(f"[GRAPH] Vertices: {num_vertices}")
    print(f"[GRAPH] Edges:    {num_edges}")

    print(f"[TIME] Grid creation: {t_grid_end - t_grid_start:.3f}s")
    print(f"[TIME] Graph build:   {t_graph_end - t_graph_start:.3f}s")

    # ---------------------------------------
    # 2. Plot hex grid (background)
    # ---------------------------------------
    t_plot_hex_start = time.perf_counter()

    fig, ax = plt.subplots(figsize=(10, 10))

    for cell in grid.iter_domain_cells():
        poly = cell.polygon
        x, y = poly.exterior.xy

        patch = MplPolygon(
            list(zip(x, y)),
            closed=True,
            edgecolor="lightgray",
            facecolor="none",
            linewidth=0.6,
            alpha=0.6,
        )
        ax.add_patch(patch)

    t_plot_hex_end = time.perf_counter()
    print(f"[TIME] HexGrid plotting: {t_plot_hex_end - t_plot_hex_start:.3f}s")

    # ---------------------------------------
    # 3. Plot graph edges (foreground)
    # ---------------------------------------
    t_plot_edges_start = time.perf_counter()

    vid_to_cell = graph["vertex_id_to_cell"]


    for e in graph.es:
        v1, v2 = e.tuple

        c1 = vid_to_cell[v1]
        c2 = vid_to_cell[v2]


        assert c1 and c2

        x = [c1.cartesian_center.x, c2.cartesian_center.x]
        y = [c1.cartesian_center.y, c2.cartesian_center.y]

        ax.plot(x, y, color="blue", linewidth=1.0, alpha=0.8)

    t_plot_edges_end = time.perf_counter()
    print(
        f"[TIME] Graph edges plotting: {t_plot_edges_end - t_plot_edges_start:.3f}s")

    # ---------------------------------------
    # 4. Plot graph vertices
    # ---------------------------------------
    t_plot_vertices_start = time.perf_counter()

    xs, ys = [], []
    for cell in vid_to_cell.values():
        xs.append(cell.cartesian_center.x)
        ys.append(cell.cartesian_center.y)

    ax.scatter(xs, ys, c="red", s=8, zorder=5)

    t_plot_vertices_end = time.perf_counter()
    print(
        f"[TIME] Graph vertices plotting: {t_plot_vertices_end - t_plot_vertices_start:.3f}s")

    # ---------------------------------------
    # 5. Styling
    # ---------------------------------------
    ax.set_aspect("equal")
    (xmin, xmax), (ymin, ymax) = grid.get_domain()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_title("HexGrid + iGraph overlay")
    ax.grid(False)

    t_total = time.perf_counter()
    print(f"[TIME] TOTAL runtime: {t_total - t0:.3f}s")

    plt.show()
