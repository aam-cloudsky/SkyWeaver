from typing import List, Optional

from shapely.geometry import Point

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.model.cells import RestrictedCells
from skyweaver.model.sites import BaseVertiports, VertiportEdit, VertiportEdits, Vertiports
from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost
from skyweaver.units.routes.route_computation import (
    build_airspace_graph,
    compute_routes,
)
from skyweaver.units.routes.vertiports import apply_vertiport_edits
from skyweaver.units.yaml_loader.parcel_conversion import configuration_of


class RoutesUnit(OperationalUnit[RoutesOutpost]):
    """Routes between the vertiports (old core). Delegates to the flow functions."""

    def __init__(self, outpost: Optional[RoutesOutpost] = None):

        if outpost is None:
            outpost = RoutesOutpost()
        super().__init__(outpost=outpost)

    def _from_cartesian_to_hex(self, cartesian: Point) -> Optional[HexCell]:
        grid = self._outpost.grid_parcel.grid
        return grid.get_cell_from_cartesian(cartesian)

    def _from_cell_to_cartesian(self, hex: HexCell):
        grid = self._outpost.grid_parcel.grid
        return grid.cartesian_cell_center(hex)

    def _apply(self, edit: VertiportEdit) -> List[Point]:
        current = BaseVertiports(points=tuple(self._outpost.vertiports_parcel.vertiports))
        edited = apply_vertiport_edits(
            current, VertiportEdits((edit,)), self._outpost.grid_parcel.grid
        )
        return list(edited.points)

    def add_vertiport(self, cell: HexCell) -> None:

        if not self._is_cell_available(cell):
            return

        vertiports = self._apply(VertiportEdit("add", cell.coord))

        with self._outpost:
            self._outpost.vertiports_parcel.vertiports = vertiports

    def remove_vertiport(self, cell: HexCell) -> None:

        before = self._outpost.vertiports_parcel.vertiports
        remaining = self._apply(VertiportEdit("remove", cell.coord))

        if len(remaining) == len(before):
            return

        with self._outpost:
            self._outpost.vertiports_parcel.vertiports = remaining

    def clear_vertiports(self) -> None:
        with self._outpost:
            self._outpost.vertiports_parcel.vertiports.clear()

    def _restricted_cells(self) -> RestrictedCells:
        grid = self._outpost.grid_parcel.grid
        return RestrictedCells(
            coords=frozenset(
                cell.coord for cell in grid.iter_domain_cells() if not cell.is_traversable
            )
        )

    def run(self) -> None:

        grid = self._outpost.grid_parcel.grid
        airspace_graph = build_airspace_graph(grid, self._restricted_cells())

        with self._outpost:
            self._outpost.routes_parcel.airspace_graph = airspace_graph

        routes = compute_routes(
            airspace_graph,
            Vertiports(points=tuple(self._outpost.vertiports_parcel.vertiports)),
            grid,
            configuration_of(self._outpost.yaml_parcel),
        )

        with self._outpost:
            self._outpost.routes_parcel.routes_graph = routes.routes_graph
            self._outpost.routes_parcel.terminals_graph = routes.terminals_graph

    # =========================================================================
    # Cells
    # =========================================================================
    def is_cell_on_route(self, cell: HexCell) -> bool:
        routes_graph = self._outpost.routes_parcel.routes_graph
        if routes_graph is None:
            return False
        for path in routes_graph.paths:
            if cell in path:
                return True
        return False

    def _is_cell_available(self, cell: HexCell):
        if not cell.is_traversable:
            return False

        if self._cell_has_heliport(cell):
            return False

        return True

    def _cell_has_heliport(self, cell: HexCell) -> bool:

        grid = self._outpost.grid_parcel.grid
        heliports = self._outpost.heliports_parcel.heliports

        for p in heliports:
            if grid.get_cell_from_cartesian(p) == cell:
                return True

        return False
