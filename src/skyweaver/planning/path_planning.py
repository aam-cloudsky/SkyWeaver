from typing import Dict, List, Tuple
import igraph as ig
from shapely import Point

from skyweaver.discretization.grid.base_cell import BaseCell
from itertools import combinations

from typing import Sequence


class PathPlanning:

    def __init__(self, graph: ig.Graph):
        self.set_graph(graph)
        


    def set_graph(self, graph: ig.Graph) -> None:
        self.graph: ig.Graph = graph
        self.terminal_graph: ig.Graph = ig.Graph()

    def path(
        self,
        start_vertex_id: int,
        end_vertex_id: int
    ) -> Tuple[List[BaseCell], float]:

        paths = self.graph.get_shortest_paths(
            v=start_vertex_id,
            to=end_vertex_id,
            weights="weight",
            output="vpath",
        )

        if not paths or not paths[0]:
            return [], float("inf")

        vpath = paths[0]

        # ----------------------------
        # Compute path cost explicitly
        # ----------------------------
        cost = 0.0
        for u, v in zip(vpath[:-1], vpath[1:]):
            eid = self.graph.get_eid(u, v)
            cost += self.graph.es[eid]["weight"]

        path_cells = [
            self.graph["vertex_id_to_cell"][vid]
            for vid in vpath
        ]

        return path_cells, cost

    
    def has_path(self, start_vertex_id: int, end_vertex_id: int) -> bool:
        """
        Check if there is a path between two vertices.

        Args:
            start_vertex_id (int): The ID of the starting vertex.
            end_vertex_id (int): The ID of the ending vertex.

        Returns:
            bool: True if a path exists, False otherwise.
        path, _ = self.path(start_vertex_id, end_vertex_id)
        """

        path, _ = self.path(start_vertex_id, end_vertex_id)
        return len(path) > 0
    
    


    def paths(self, terminals: Sequence[BaseCell]) -> ig.Graph:
        """
        Compute the shortest paths between multiple terminal cells.

        Args:
            terminals (List[BaseCell]): A list of terminal cells.

        Returns:
            ig.Graph: A graph where vertices represent terminal cells and
                    edges represent shortest paths in the base graph.
        """

        if len(terminals) < 2:
            raise ValueError("At least two terminal cells are required.")

        # --------------------------------------------------
        # 1. Create terminal graph vertices (1 per terminal)
        # --------------------------------------------------
        sub_graph = ig.Graph(directed=False)

        terminal_to_vid: Dict[BaseCell, int] = {}
        vid_to_terminal: Dict[int, BaseCell] = {}

        for cell in terminals:
            vid = sub_graph.vcount()
            sub_graph.add_vertex()
            terminal_to_vid[cell] = vid
            vid_to_terminal[vid] = cell

        sub_graph["cell_to_vertex_id"] = terminal_to_vid
        sub_graph["vertex_id_to_cell"] = vid_to_terminal

        # --------------------------------------------------
        # 2. Compute shortest paths between terminal pairs
        # --------------------------------------------------
        for cell_a, cell_b in combinations(terminals, 2):

            v_a = self.cell_to_vertex_id(cell_a)
            v_b = self.cell_to_vertex_id(cell_b)

            path_cells, distance = self.path(v_a, v_b)

            if not path_cells:
                continue

            sub_graph.add_edge(
                terminal_to_vid[cell_a],
                terminal_to_vid[cell_b],
                weight=distance,
                path=path_cells,  # real path in base graph
            )

        return sub_graph




    def cells_to_vertex_ids(self, cells: List[BaseCell]) -> List[int]:
        cell_to_vertex_id: Dict[BaseCell, int] = self.graph["cell_to_vertex_id"]
        vertex_ids = [cell_to_vertex_id[cell] for cell in cells]
        return vertex_ids

    def cell_to_vertex_id(self, cell: BaseCell) -> int:
        cell_to_vertex_id: Dict[BaseCell, int] = self.graph["cell_to_vertex_id"]
        return cell_to_vertex_id[cell]


if __name__ == "__main__":

    import random
    import time
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    from skyweaver.discretization.grid.hexgrid.hexgrid import HexGrid
    from skyweaver.planning.graph.graph_configuration import GraphConfiguration
    from skyweaver.planning.graph.graph_builder import GraphBuilder
    from skyweaver.planning.path_planning import PathPlanning

    EMPTY_POINT = [[float("nan"), float("nan")]]


    # ======================================================
    # 1. Build grid
    # ======================================================
    grid = HexGrid(cell_size=100.0)

    # ======================================================
    # 2. Build graph from grid
    # ======================================================
    config = GraphConfiguration()
    builder = GraphBuilder(config)
    graph = builder.build()

    print(f"[GRAPH] vertices={graph.vcount()} edges={graph.ecount()}")

    # ======================================================
    # 3. Path planner
    # ======================================================
    planner = PathPlanning(graph)

    # ======================================================
    # 4. Pick random fixed terminals
    # ======================================================
    all_cells = list(grid.iter_domain_cells())
    available_cells = [c for c in all_cells if c.available]

    NUM_TERMINALS = 3
    fixed_terminals = random.sample(available_cells, NUM_TERMINALS)

    print("[FIXED TERMINALS]")
    for c in fixed_terminals:
        print(f"  {c.coord}")

    # ======================================================
    # 5. Matplotlib setup
    # ======================================================
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.set_aspect("equal")

    (xmin, xmax), (ymin, ymax) = grid.get_domain()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_title("HexGrid + Graph + All-Pairs Dynamic Path Planning")

    # ======================================================
    # 6. Plot hex grid
    # ======================================================
    for cell in all_cells:
        poly = cell.polygon.exterior.coords
        ax.add_patch(
            MplPolygon(
                poly,
                closed=True,
                edgecolor="lightgray",
                facecolor="none",
                linewidth=0.8,
            )
        )

    # ======================================================
    # 7. Plot graph edges
    # ======================================================
    vid_to_cell = graph["vertex_id_to_cell"]

    for e in graph.es:
        v1, v2 = e.tuple
        c1 = vid_to_cell[v1]
        c2 = vid_to_cell[v2]

        ax.plot(
            [c1.cartesian_center.x, c2.cartesian_center.x],
            [c1.cartesian_center.y, c2.cartesian_center.y],
            color="lightblue",
            linewidth=1,
            alpha=0.5,
        )

    # ======================================================
    # 8. Plot fixed terminals
    # ======================================================
    ax.scatter(
        [c.cartesian_center.x for c in fixed_terminals],
        [c.cartesian_center.y for c in fixed_terminals],
        c="green",
        s=80,
        zorder=5,
        label="Fixed terminals",
    )

    # ======================================================
    # 9. Dynamic plot elements
    # ======================================================
    path_line, = ax.plot([], [], color="red", linewidth=3, zorder=6)
    mouse_point = ax.scatter([], [], c="red", s=60, zorder=7)

    # ======================================================
    # 10. Mouse callback (ALL-PAIRS)
    # ======================================================
    def on_mouse_move(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            path_line.set_data([], [])
            mouse_point.set_offsets(EMPTY_POINT)
            fig.canvas.draw_idle()
            return

        cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
        if cell is None or not cell.available:
            path_line.set_data([], [])
            mouse_point.set_offsets(EMPTY_POINT)
            fig.canvas.draw_idle()
            return

        mouse_point.set_offsets([
            [cell.cartesian_center.x, cell.cartesian_center.y]
        ])

        # resto do cálculo...


        terminals = fixed_terminals + [cell]

        t0 = time.perf_counter()

        terminal_graph = planner.paths(terminals)

        xs, ys = [], []
        for e in terminal_graph.es:
            for c in e["path"]:
                xs.append(c.cartesian_center.x)
                ys.append(c.cartesian_center.y)
            xs.append(None)
            ys.append(None)

        dt_ms = (time.perf_counter() - t0) * 1000.0
        print(f"[ALL-PAIRS UPDATE] {dt_ms:.2f} ms")

        path_line.set_data(xs, ys)
        fig.canvas.draw_idle()

    # ======================================================
    # 11. Connect and show
    # ======================================================
    fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
    ax.legend()
    plt.show()
