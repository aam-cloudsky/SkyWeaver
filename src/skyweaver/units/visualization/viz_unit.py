from typing import Callable, Optional, List

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import numpy as np

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.analysis.metrics import average_path_length, betweenness
from skyweaver.units.visualization.logistics.viz_outpost import VizOutpost
from skyweaver.units.grid.geometry.basecell import BaseCell


class VisualizationUnit(OperationalUnit[VizOutpost]):
    def __init__(
        self,
        outpost: Optional[VizOutpost] = None,
        on_left_click: Optional[Callable[[BaseCell], None]] = None,
        on_right_click: Optional[Callable[[BaseCell], None]] = None,
    ):
        if outpost is None:
            outpost = VizOutpost()
        super().__init__(outpost)
        self._fig, self._ax = plt.subplots(figsize=(10, 10))
        self._ax.set_aspect("equal")
        self._grid_patches = {}
        self._dynamic_artists: list = []
        self._on_left_click = on_left_click
        self._on_right_click = on_right_click

        self._heliports_scatter = self._ax.scatter(
            [], [], c="red", s=110, zorder=7, label="Heliports"
        )
        self._vertiports_scatter = self._ax.scatter(
            [], [], c="orange", s=110, zorder=7, label="Vertiports (terminals)"
        )

        self._apl_text = self._ax.text(
            0.02,
            0.98,
            "APL: 0.0",
            transform=self._ax.transAxes,
            ha="left",
            va="top",
            fontsize=10,
            bbox=dict(
                boxstyle="round,pad=0.25",
                facecolor="white",
                edgecolor="lightgray",
                alpha=0.9,
            ),
        )

        self._ax.legend()
        self._fig.canvas.mpl_connect("button_press_event", self._handle_click)

    def run(self) -> None:
        """
        Redesenha tudo baseado no estado atual do outpost.
        """
        self._clear_dynamic()

        grid = self._outpost.grid_parcel.grid

        heliports_cells: List[BaseCell] = grid.get_cell_from_cartesians(
            self._outpost.heliports_parcel.heliports
        )
        vertiports_cells: List[BaseCell] = grid.get_cell_from_cartesians(
            self._outpost.vertiports_parcel.vertiports
        )

        routes_graph = self._outpost.routes_parcel.routes_graph

        self._update_grid(grid)
        self._update_vertiports(vertiports_cells)
        self._update_heliports(heliports_cells)
        self._update_routes(routes_graph)
        self._update_metrics(routes_graph)
        self._ax.legend()
        self._fig.canvas.draw_idle()

    def show(self) -> None:
        self._fig.canvas.draw_idle()
        plt.show()

    def _update_metrics(self, routes_graph) -> None:
        # APL
        if routes_graph:
            apl_result = average_path_length(routes_graph)
            self._apl_text.set_text(f"APL: {apl_result:.3f}")
        else:
            self._apl_text.set_text("APL: 0.0")

        # Betweenness por célula
        if routes_graph:
            betw_result = betweenness(routes_graph)
            for cell_v, value in betw_result.items():
                if value == 0:
                    continue
                txt = self._ax.text(
                    cell_v.cartesian_center.x,
                    cell_v.cartesian_center.y,
                    f"{int(value)}",
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
                    ),
                )
                self._dynamic_artists.append(txt)

    def _clear_dynamic(self) -> None:
        for artist in self._dynamic_artists:
            artist.remove()
        self._dynamic_artists.clear()

    def _update_routes(self, routes_graph) -> None:
        if routes_graph is None:
            return

        g = routes_graph.graph
        for e in g.es:
            v1, v2 = e.tuple
            c1 = g.vs[v1]["cell"]
            c2 = g.vs[v2]["cell"]
            xs = [c1.cartesian_center.x, c2.cartesian_center.x]
            ys = [c1.cartesian_center.y, c2.cartesian_center.y]
            (line,) = self._ax.plot(xs, ys, color="blue", linewidth=3.0, alpha=0.85)
            self._dynamic_artists.append(line)

    def _update_grid(self, grid) -> None:
        for cell in grid.iter_domain_cells():
            patch = self._grid_patches.get(cell)
            if patch is None:
                patch = MplPolygon(
                    cell.polygon.exterior.coords,
                    closed=True,
                    edgecolor="lightgray",
                    facecolor="none",
                    linewidth=0.8,
                )
                self._ax.add_patch(patch)
                self._grid_patches[cell] = patch
            else:
                patch.set_facecolor("lightcoral" if not cell.available else "none")

        self._fig.canvas.draw_idle()

    def _update_heliports(self, heliports_cells: List[BaseCell]) -> None:
        pts = np.array(
            [[c.cartesian_center.x, c.cartesian_center.y] for c in heliports_cells],
            dtype=float,
        )
        if pts.size == 0:
            pts = np.empty((0, 2), dtype=float)
        self._heliports_scatter.set_offsets(pts)

    def _update_vertiports(self, vertiports_cells: List[BaseCell]) -> None:
        pts = np.array(
            [[c.cartesian_center.x, c.cartesian_center.y] for c in vertiports_cells],
            dtype=float,
        )
        if pts.size == 0:
            pts = np.empty((0, 2), dtype=float)
        self._vertiports_scatter.set_offsets(pts)

    def _handle_click(self, event) -> None:
        if event.inaxes != self._ax or event.xdata is None or event.ydata is None:
            return

        grid = self._outpost.grid_parcel.grid
        cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
        if cell is None:
            return

        if event.button == 1 and self._on_left_click:
            self._on_left_click(cell)
        elif event.button == 3 and self._on_right_click:
            self._on_right_click(cell)
