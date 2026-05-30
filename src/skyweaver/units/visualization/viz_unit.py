from typing import Callable, Optional, List, Any

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
import numpy as np

from shapely.geometry import Point

from types import ModuleType
from typing import cast

try:
    import contextily as _ctx

    ctx: ModuleType | None = _ctx
except Exception:  # pragma: no cover
    ctx = None

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.analysis.metrics import average_path_length, betweenness
from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.visualization.logistics.viz_outpost import VizOutpost
import math


class VisualizationUnit(OperationalUnit[VizOutpost]):
    def __init__(
        self,
        outpost: Optional[VizOutpost] = None,
        on_left_click: Optional[Callable[[HexCell], None]] = None,
        on_right_click: Optional[Callable[[HexCell], None]] = None,
        enable_basemap: bool = True,
        basemap_provider: Optional[Any] = None,
        basemap_alpha: float = 1.0,
        basemap_zorder: int = 0,
        show_grid: bool = True,
        show_routes: bool = True,
        show_apl: bool = True,
        show_betweenness: bool = False,
        show_heliports: bool = True,
        show_vertiports: bool = True,
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

        # Basemap (optional). Requires: contextily + a Domain in the outpost.
        self._enable_basemap = enable_basemap
        self._basemap_provider = basemap_provider
        self._basemap_alpha = basemap_alpha
        self._basemap_zorder = basemap_zorder
        self._basemap_drawn = False

        # Visualization toggles
        self._show_grid = show_grid
        self._show_routes = show_routes
        self._show_apl = show_apl
        self._show_betweenness = show_betweenness
        self._show_heliports = show_heliports
        self._show_vertiports = show_vertiports

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
        # Optional: draw OSM basemap and switch axes to projected CRS.
        self._maybe_setup_basemap(grid)

        heliports_cells: List[HexCell] = grid.get_cell_from_cartesians(
            self._outpost.heliports_parcel.heliports
        )
        vertiports_cells: List[HexCell] = grid.get_cell_from_cartesians(
            self._outpost.vertiports_parcel.vertiports
        )

        routes_graph = self._outpost.routes_parcel.routes_graph

        if self._show_grid:
            self._update_grid(grid)

        if self._show_vertiports:
            self._update_vertiports(vertiports_cells)
        else:
            self._vertiports_scatter.set_offsets(np.empty((0, 2)))

        if self._show_heliports:
            self._update_heliports(heliports_cells)
        else:
            self._heliports_scatter.set_offsets(np.empty((0, 2)))

        if self._show_routes:
            self._update_routes(routes_graph)

        self._update_metrics(routes_graph)
        self._ax.legend()
        self._fig.canvas.draw_idle()

    def _marker_area_from_cell(
        self, cell: HexCell, radius_factor: float = 0.25
    ) -> float:
        grid = self._outpost.grid_parcel.grid
        cx, cy = self._cell_center_xy(grid, cell)

        radius_data = cell.size * radius_factor

        x0, y0 = self._ax.transData.transform((cx, cy))
        x1, y1 = self._ax.transData.transform((cx + radius_data, cy))

        radius_pixels = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        radius_points = radius_pixels * 72.0 / self._fig.dpi

        return math.pi * (radius_points**2)

    def show(self) -> None:
        self._fig.canvas.draw_idle()
        plt.show()

    def _try_get_domain(self):
        """Best-effort access to Domain without hard-coupling VizOutpost schema."""
        if not hasattr(self._outpost, "domain_parcel"):
            return None
        domain_parcel = getattr(self._outpost, "domain_parcel")
        if domain_parcel is None:
            return None
        return getattr(domain_parcel, "domain", None)

    def _try_get_local_frame(self):
        domain = self._try_get_domain()
        if domain is None:
            return None
        return getattr(domain, "_local_frame", None)

    def _is_projected_mode(self) -> bool:
        """If basemap is enabled and we have a local frame, we draw in projected CRS."""
        return bool(
            self._enable_basemap
            and ctx is not None
            and self._try_get_local_frame() is not None
        )

    def _local_xy_to_projected(self, x: float, y: float) -> tuple[float, float]:
        lf = self._try_get_local_frame()
        if lf is None:
            return x, y

        gdf = lf.to_crs([Point(x, y)])
        p = gdf.geometry.iloc[0]
        return (float(p.x), float(p.y))

    def _maybe_setup_basemap(self, grid: HexGrid) -> None:
        if not self._is_projected_mode():
            return
        if self._basemap_drawn:
            return

        ctx_mod = cast(Any, ctx)
        domain = self._try_get_domain()
        lf = self._try_get_local_frame()
        if domain is None or lf is None:
            return

        # --------------------------------------------------
        # 1️⃣ Compute projected bounds from local grid bounds
        # --------------------------------------------------
        domain_bounds = grid.domain_bounds()

        gdf = lf.to_crs(domain_bounds.corners)

        xs = [p.x for p in gdf.geometry]
        ys = [p.y for p in gdf.geometry]

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        self._ax.set_xlim(xmin, xmax)
        self._ax.set_ylim(ymin, ymax)

        # --------------------------------------------------
        # 2️⃣ Choose provider correctly
        # --------------------------------------------------
        provider = self._basemap_provider
        if provider is None:
            provider = ctx_mod.providers.OpenStreetMap.Mapnik

        # --------------------------------------------------
        # 3️⃣ Draw basemap
        # --------------------------------------------------
        ctx_mod.add_basemap(
            self._ax,
            crs=domain.crs,
            source=provider,
            alpha=self._basemap_alpha,
            zorder=self._basemap_zorder,
        )

        self._basemap_drawn = True

    def _cell_center_xy(self, grid: HexGrid, cell: HexCell) -> tuple[float, float]:
        center = grid.cartesian_cell_center(cell)
        x, y = center.x, center.y
        if self._is_projected_mode():
            return self._local_xy_to_projected(x, y)
        return x, y

    def _cells_to_offsets(self, grid, cells: List[HexCell]) -> np.ndarray:
        if not cells:
            return np.empty((0, 2), dtype=float)
        pts = np.array([self._cell_center_xy(grid, c) for c in cells], dtype=float)
        return pts

    def _update_metrics(self, routes_graph) -> None:
        # APL
        if self._show_apl and routes_graph:
            apl_result = average_path_length(routes_graph)
            self._apl_text.set_text(f"APL: {apl_result:.3f}")
            self._apl_text.set_visible(True)
        else:
            self._apl_text.set_visible(False)

        # Betweenness por célula
        if self._show_betweenness and routes_graph:
            grid = self._outpost.grid_parcel.grid
            betw_result = betweenness(routes_graph)

            for cell_v, value in betw_result.items():
                if value == 0:
                    continue

                x, y = self._cell_center_xy(grid, cell_v)

                txt = self._ax.text(
                    x,
                    y,
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

        grid = self._outpost.grid_parcel.grid

        g = routes_graph.graph
        for e in g.es:
            v1, v2 = e.tuple
            c1 = g.vs[v1]["cell"]
            c2 = g.vs[v2]["cell"]
            x1, y1 = self._cell_center_xy(grid, c1)
            x2, y2 = self._cell_center_xy(grid, c2)
            xs = [x1, x2]
            ys = [y1, y2]
            (line,) = self._ax.plot(xs, ys, color="blue", linewidth=3.0, alpha=0.85)
            self._dynamic_artists.append(line)

    def _update_grid(self, grid: HexGrid) -> None:
        for cell in grid.iter_domain_cells():
            patch = self._grid_patches.get(cell)
            if patch is None:
                polygon = grid.cell_polygon(cell)
                coords = list(polygon.exterior.coords)
                if self._is_projected_mode():
                    coords = [self._local_xy_to_projected(x, y) for (x, y) in coords]
                patch = MplPolygon(
                    coords,
                    closed=True,
                    edgecolor="lightgray",
                    facecolor="none",
                    linewidth=0.8,
                )
                self._ax.add_patch(patch)
                self._grid_patches[cell] = patch
            # else:
            patch.set_facecolor("lightcoral" if not cell.is_traversable else "none")

        self._fig.canvas.draw_idle()

    def _update_heliports(self, heliports_cells: List[HexCell]) -> None:
        grid = self._outpost.grid_parcel.grid
        pts = self._cells_to_offsets(grid, heliports_cells)
        self._heliports_scatter.set_offsets(pts)

        if heliports_cells:
            area = self._marker_area_from_cell(heliports_cells[0], radius_factor=0.22)
            self._heliports_scatter.set_sizes([area] * len(heliports_cells))
        else:
            self._heliports_scatter.set_sizes([])

    def _update_vertiports(self, vertiports_cells: List[HexCell]) -> None:
        grid = self._outpost.grid_parcel.grid
        pts = self._cells_to_offsets(grid, vertiports_cells)
        self._vertiports_scatter.set_offsets(pts)

        if vertiports_cells:
            area = self._marker_area_from_cell(vertiports_cells[0], radius_factor=0.22)
            self._vertiports_scatter.set_sizes([area] * len(vertiports_cells))
        else:
            self._vertiports_scatter.set_sizes([])

    def _handle_click(self, event) -> None:
        if event.inaxes != self._ax or event.xdata is None or event.ydata is None:
            return

        grid = self._outpost.grid_parcel.grid
        cell = grid.get_cell_from_cartesian(Point(event.xdata, event.ydata))
        if cell is None:
            return

        if event.button == 1 and self._on_left_click:
            self._on_left_click(cell)
        elif event.button == 3 and self._on_right_click:
            self._on_right_click(cell)
