from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from shapely.geometry import Point

from skyweaver.core.logistics.depot import Depot
from skyweaver.units.domain.domain_unit import DomainUnit
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.routes.routes_unit import RoutesUnit
from skyweaver.units.sources.sources_unit import SourcesUnit
from skyweaver.units.visualization.viz_unit import VisualizationUnit


@dataclass
class RoutesApp:
    cell_size: float = 100.0

    def __post_init__(self) -> None:
        self.depot = Depot()

        self.sources = SourcesUnit()
        self.domain = DomainUnit()
        self.routes = RoutesUnit()

        self.viz = VisualizationUnit(
            on_left_click=self.on_left_click,
            on_right_click=self.on_right_click,
        )

        self.grid: Optional[HexGrid] = None

    def setup(self) -> None:
        # 1) load/simulate sources
        self.sources.run()

        # 2) compute domain based on sources
        self.domain.run()

        # 3) build grid (consumes domain via depot sync)
        self.grid = HexGrid(cell_size=self.cell_size)

        # 4) apply heliport restrictions on grid
        self._apply_heliport_restrictions()

        # 5) build routes and draw
        self.routes.rebuild_airspace_graph()
        self.routes.run()
        self.viz.run()
        self.viz.show()

    # ------------------------------------------------------------------
    # Policies / Actions
    # ------------------------------------------------------------------

    def on_left_click(self, cell) -> None:
        # toggle terminal (vertiport) if not restricted
        if cell is None or not cell.available:
            return
        if self._is_heliport_cell(cell):
            return

        if self._is_vertiport_cell(cell):
            self._remove_vertiport(cell)
        else:
            self._add_vertiport(cell)

        self.routes.run()
        self.viz.run()

    def on_right_click(self, cell) -> None:
        # toggle restriction (not allowed on terminals/heliports)
        if cell is None:
            return
        if self._is_heliport_cell(cell) or self._is_vertiport_cell(cell):
            return

        cell.set_availability(not cell.available)

        if self.routes.is_cell_on_route(cell):
            self.routes.rebuild_airspace_graph()
            self.routes.run()
            self.viz.run()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_heliport_restrictions(self) -> None:
        if self.grid is None:
            return
        heliport_cells = self.grid.get_cell_from_cartesians(
            self.sources._outpost.heliports_parcel.heliports
        )
        for cell in heliport_cells:
            cell.set_unavailable()

    def _is_heliport_cell(self, cell) -> bool:
        if self.grid is None:
            return False
        heliport_cells = self.grid.get_cell_from_cartesians(
            self.sources._outpost.heliports_parcel.heliports
        )
        return cell in heliport_cells

    def _is_vertiport_cell(self, cell) -> bool:
        if self.grid is None:
            return False
        vertiport_cells = self.grid.get_cell_from_cartesians(
            self.sources._outpost.vertiports_parcel.vertiports
        )
        return cell in vertiport_cells

    def _add_vertiport(self, cell) -> None:
        pt = Point(cell.cartesian_center.x, cell.cartesian_center.y)
        with self.sources._outpost:
            self.sources._outpost.vertiports_parcel.vertiports.append(pt)

    def _remove_vertiport(self, cell) -> None:
        target = Point(cell.cartesian_center.x, cell.cartesian_center.y)
        with self.sources._outpost:
            verts = self.sources._outpost.vertiports_parcel.vertiports
            for i, pt in enumerate(verts):
                if pt.equals(target):
                    del verts[i]
                    break
