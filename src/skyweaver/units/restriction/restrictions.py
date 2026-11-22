"""Which cells no route may cross."""

from __future__ import annotations

from skyweaver.model.cells import HeliportCells, RestrictedCells, RestrictionToggles
from skyweaver.model.sites import Heliports
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid


def locate_heliport_cells(heliports: Heliports, grid: HexGrid) -> HeliportCells:
    """The cells that contain a heliport (heliports outside the grid are ignored)."""

    cells = grid.get_cell_from_cartesians(heliports.points)
    return HeliportCells(coords=frozenset(cell.coord for cell in cells))


def restrict_cells(
    heliport_cells: HeliportCells, toggles: RestrictionToggles
) -> RestrictedCells:
    """Heliport cells are always restricted; the user restricts the others."""

    return RestrictedCells(coords=heliport_cells.coords | toggles.coords)
