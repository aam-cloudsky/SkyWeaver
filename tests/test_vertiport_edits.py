"""The fold of VertiportEdits reproduces the vertiport list of the old core.

`legacy_add` and `legacy_remove` are the list operations of
`RoutesUnit.add_vertiport` and `RoutesUnit.remove_vertiport` at `cd02743`:
add appends the center of the cell; remove keeps the vertiports whose cell
differs, pairing each vertiport with its cell.
"""

from __future__ import annotations

from shapely.geometry import Point

from conftest import xy
from skyweaver.model import BaseVertiports, VertiportEdit, VertiportEdits, Vertiports
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.routes.vertiports import apply_vertiport_edits


def legacy_add(vertiports: list[Point], grid: HexGrid, coord: HexCoord) -> list[Point]:
    cell = grid.get_cell_from_coord(coord)
    return vertiports + [grid.cartesian_cell_center(cell)]


def legacy_remove(vertiports: list[Point], grid: HexGrid, coord: HexCoord) -> list[Point]:
    cell = grid.get_cell_from_coord(coord)
    cells = grid.get_cell_from_cartesians(vertiports)
    return [v for v, c in zip(vertiports, cells) if c != cell]


def legacy(base: BaseVertiports, grid: HexGrid, edits: list[VertiportEdit]) -> list[Point]:
    points = list(base.points)
    for edit in edits:
        operation = legacy_add if edit.kind == "add" else legacy_remove
        points = operation(points, grid, edit.coord)
    return points


def free_coord(rio, grid: HexGrid) -> HexCoord:
    """A domain cell with no heliport and no vertiport."""

    taken = set(rio.heliport_cells.coords) | {
        cell.coord for cell in grid.get_cell_from_cartesians(rio.base.points)
    }
    return next(cell.coord for cell in grid.iter_domain_cells() if cell.coord not in taken)


def fold(rio, grid: HexGrid, edits: list[VertiportEdit]) -> Vertiports:
    return apply_vertiport_edits(rio.base, VertiportEdits(tuple(edits)), grid)


def check(rio, edits: list[VertiportEdit]) -> Vertiports:
    grid = rio.grid()
    result = fold(rio, grid, edits)
    assert xy(result.points) == xy(legacy(rio.base, grid, edits))
    return result


def test_no_edit_gives_the_base_list(rio) -> None:
    result = check(rio, [])
    assert xy(result.points) == xy(rio.base.points)


def test_add_appends_the_cell_center(rio) -> None:
    grid = rio.grid()
    coord = free_coord(rio, grid)
    result = check(rio, [VertiportEdit("add", coord)])
    assert len(result.points) == len(rio.base.points) + 1
    assert grid.get_cell_from_cartesian(result.points[-1]).coord == coord


def test_add_then_remove_restores_the_base_list(rio) -> None:
    coord = free_coord(rio, rio.grid())
    result = check(rio, [VertiportEdit("add", coord), VertiportEdit("remove", coord)])
    assert xy(result.points) == xy(rio.base.points)


def test_re_add_of_the_same_cell_goes_to_the_end(rio) -> None:
    grid = rio.grid()
    first = grid.get_cell_from_cartesian(rio.base.points[0]).coord
    coord = free_coord(rio, grid)
    result = check(
        rio,
        [
            VertiportEdit("add", coord),
            VertiportEdit("remove", first),
            VertiportEdit("add", first),
            VertiportEdit("remove", coord),
            VertiportEdit("add", coord),
        ],
    )
    cells = [grid.get_cell_from_cartesian(p).coord for p in result.points]
    assert cells[-2:] == [first, coord]


def test_removal_of_a_base_vertiport(rio) -> None:
    grid = rio.grid()
    coord = grid.get_cell_from_cartesian(rio.base.points[3]).coord
    result = check(rio, [VertiportEdit("remove", coord)])
    assert len(result.points) == len(rio.base.points) - 1
    assert coord not in {grid.get_cell_from_cartesian(p).coord for p in result.points}


def test_remove_drops_every_vertiport_of_the_cell(rio) -> None:
    coord = free_coord(rio, rio.grid())
    result = check(
        rio,
        [VertiportEdit("add", coord), VertiportEdit("add", coord), VertiportEdit("remove", coord)],
    )
    assert xy(result.points) == xy(rio.base.points)


def test_edits_and_results_are_new_values(rio) -> None:
    edits = VertiportEdits()
    coord = free_coord(rio, rio.grid())
    longer = edits.appended(VertiportEdit("add", coord))
    assert edits.edits == () and len(longer.edits) == 1
    assert isinstance(fold(rio, rio.grid(), list(longer.edits)).points, tuple)
