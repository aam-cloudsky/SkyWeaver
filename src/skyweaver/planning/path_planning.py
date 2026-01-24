
from typing import Iterable, List
from dataclasses import dataclass

from typing import Dict, List, Tuple
import igraph as ig

from skyweaver.core.logistics.depot import Depot
from skyweaver.discretization.grid.base_cell import BaseCell
from itertools import combinations

from typing import Sequence

from enum import Enum


class PathPlanning:


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
    planner: PathPlanning,
    terminals: Iterable[BaseCell],
) -> List[List[BaseCell]]:
    """
    Compute shortest paths between all terminal pairs (G0 → paths).

    Returns:
        List of paths (each path is a list of BaseCell)
    """
    paths: List[List[BaseCell]] = []

    for a, b in combinations(terminals, 2):
        cost, cells = planner.shortest_path(a, b)
        if cells is not None:
            paths.append(cells)

    return paths


if __name__ == "__main__":

    import random
    import time
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    from skyweaver.discretization.grid.hexgrid.hexgrid import HexGrid
    from skyweaver.planning.graph.graph_outpost import GraphOutpost
    from skyweaver.planning.graph.graph_builder import GraphBuilder

    random.seed(42)
    depot = Depot()
    # ======================================================
    # 1. Build grid
    # ======================================================
    grid = HexGrid(cell_size=100.0)
    all_cells = list(grid.iter_domain_cells())

    # ======================================================
    # 2. Pick fixed terminals
    # ======================================================
    available_cells = [c for c in all_cells if c.available]
    NUM_TERMINALS = 3
    fixed_terminals = random.sample(available_cells, NUM_TERMINALS)
    fixed_terminal_set = set(fixed_terminals)

    # ======================================================
    # 3. Randomly block cells (excluding terminals)
    # ======================================================
    BLOCK_RATIO = 0.15
    candidates = [c for c in all_cells if c not in fixed_terminal_set]
    blocked = random.sample(candidates, int(len(candidates) * BLOCK_RATIO))

    for c in blocked:
        c.set_unavailable()

    # ======================================================
    # 4. Build base graph (G0)
    # ======================================================
    outpost = GraphOutpost()
    builder = GraphBuilder(outpost=outpost)
    base_graph = builder.build_navigation_graph()
    planner = PathPlanning(base_graph)

    print(
        f"[GRAPH] vertices={base_graph.vcount()} edges={base_graph.ecount()}"
    )

    # ======================================================
    # 5. Matplotlib setup
    # ======================================================
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect("equal")

    (xmin, xmax), (ymin, ymax) = grid.get_domain()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_title("Dynamic paths graph (G1 → G2) with betweenness")

    # ======================================================
    # 6. Plot hex grid
    # ======================================================
    for cell in all_cells:
        poly = cell.polygon.exterior.coords
        face = "lightcoral" if not cell.available else "none"

        ax.add_patch(
            MplPolygon(
                poly,
                closed=True,
                edgecolor="lightgray",
                facecolor=face,
                linewidth=0.8,
            )
        )

    # ======================================================
    # 7. Plot fixed terminals
    # ======================================================
    ax.scatter(
        [c.cartesian_center.x for c in fixed_terminals],
        [c.cartesian_center.y for c in fixed_terminals],
        c="green",
        s=140,
        zorder=7,
        label="Fixed terminals",
    )

    # ======================================================
    # 8. Dynamic artists
    # ======================================================
    dynamic_artists: list = []

    mouse_point = ax.scatter(
        [],
        [],
        c="black",
        s=80,
        zorder=8,
        label="Mouse terminal",
    )

    # ======================================================
    # 9. Mouse callback
    # ======================================================
    def on_mouse_move(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)

        if (
            cell is None
            or not cell.available
            or cell in fixed_terminal_set
        ):
            return

        # Update mouse marker
        mouse_point.set_offsets([
            [cell.cartesian_center.x, cell.cartesian_center.y]
        ])

        # Clear previous drawings
        for artist in dynamic_artists:
            artist.remove()
        dynamic_artists.clear()

        terminals = fixed_terminals + [cell]

        # --------------------------------------------------
        # Compute terminal paths (G0 → G1)
        # --------------------------------------------------
        t0 = time.perf_counter()

        paths = compute_terminal_paths(planner, terminals)

        if not paths:
            fig.canvas.draw_idle()
            return

        # --------------------------------------------------
        # Build paths graph (G1 → G2)
        # --------------------------------------------------
        g2 = builder.build_path_induced_graph(paths)

        # --------------------------------------------------
        # Plot G2 edges
        # --------------------------------------------------
        for e in g2.es:
            v1, v2 = e.tuple
            c1 = g2.vs[v1]["cell"]
            c2 = g2.vs[v2]["cell"]

            xs = [c1.cartesian_center.x, c2.cartesian_center.x]
            ys = [c1.cartesian_center.y, c2.cartesian_center.y]

            line, = ax.plot(
                xs,
                ys,
                color="blue",
                linewidth=3.0,
                alpha=0.85,
                zorder=5,
            )
            dynamic_artists.append(line)

        # --------------------------------------------------
        # Betweenness (intermediates only)
        # --------------------------------------------------
        bet = g2.betweenness()

        for v, b in zip(g2.vs, bet):

            if v["is_terminal"]:
                continue

            cell_v = v["cell"]

            txt = ax.text(
                cell_v.cartesian_center.x,
                cell_v.cartesian_center.y,
                f"{b:.2f}",
                fontsize=9,
                color="darkred",
                ha="center",
                va="center",
                zorder=9,
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor="white",
                    edgecolor="none",
                    alpha=0.7,
                )
            )
            dynamic_artists.append(txt)

        dt_ms = (time.perf_counter() - t0) * 1000.0
        print(f"[UPDATE] {dt_ms:.2f} ms")

        fig.canvas.draw_idle()

    # ======================================================
    # 10. Connect mouse
    # ======================================================
    fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
    ax.legend()
    plt.show()
