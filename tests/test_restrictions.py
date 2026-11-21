"""restrict_cells gives the cells the old core marked as not traversable.

The old core marked the heliport cells with `set_restricted` (RestrictionUnit)
and flipped a toggled cell between `set_restricted` and `set_available`
(ToggleRestrictionHandler). Here the same marks are applied to a fresh grid
and the non-traversable cells are compared with `restrict_cells`.
"""

from __future__ import annotations

import pytest

from skyweaver.model import HeliportCells, RestrictedCells, RestrictionToggles
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.restriction.restrictions import (
    locate_heliport_cells,
    restrict_cells,
)


def legacy_marks(rio, grid: HexGrid, toggles: list[HexCoord]) -> frozenset[HexCoord]:
    for cell in grid.get_cell_from_cartesians(rio.heliports.points):
        cell.set_restricted()
    for coord in toggles:
        cell = grid.get_cell_from_coord(coord)
        if cell.is_traversable:
            cell.set_restricted()
        else:
            cell.set_available()
    return frozenset(c.coord for c in grid.iter_domain_cells() if not c.is_traversable)


def free_coords(rio, grid: HexGrid, n: int) -> list[HexCoord]:
    coords = [
        c.coord for c in grid.iter_domain_cells() if c.coord not in rio.heliport_cells.coords
    ]
    return coords[100 : 100 + n]


def apply(toggles: list[HexCoord]) -> RestrictionToggles:
    value = RestrictionToggles()
    for coord in toggles:
        value = value.toggled(coord)
    return value


@pytest.mark.parametrize(
    "pattern", [[], [0], [0, 0], [0, 1], [0, 1, 0], [0, 1, 2, 1, 0, 2]]
)
def test_restrict_cells_equals_the_old_marks(rio, pattern: list[int]) -> None:
    grid = rio.grid()
    coords = free_coords(rio, grid, 3)
    toggles = [coords[i] for i in pattern]
    expected = legacy_marks(rio, rio.grid(), toggles)
    result = restrict_cells(rio.heliport_cells, apply(toggles))
    assert isinstance(result, RestrictedCells)
    assert result.coords == expected


def test_heliport_cells_are_always_restricted(rio) -> None:
    coords = free_coords(rio, rio.grid(), 2)
    for toggles in ([], coords, coords + coords):
        assert rio.heliport_cells.coords <= restrict_cells(
            rio.heliport_cells, apply(toggles)
        ).coords


def test_toggle_on_then_off(rio) -> None:
    coord = free_coords(rio, rio.grid(), 1)[0]
    on = RestrictionToggles().toggled(coord)
    off = on.toggled(coord)
    assert coord in restrict_cells(rio.heliport_cells, on).coords
    assert coord not in restrict_cells(rio.heliport_cells, off).coords
    assert off == RestrictionToggles()


def test_heliport_cells_of_the_case_study(rio) -> None:
    located = locate_heliport_cells(rio.heliports, rio.grid())
    assert isinstance(located, HeliportCells)
    assert located == rio.heliport_cells
    assert 0 < len(located.coords) <= len(rio.heliports.points)
