"""The vertiport list: the candidates kept, then the user's edits."""

from __future__ import annotations

from skyweaver.model.cells import HeliportCells
from skyweaver.model.sites import (
    BaseVertiports,
    CandidateVertiports,
    VertiportEdits,
    Vertiports,
)
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid


def filter_candidate_vertiports(
    candidates: CandidateVertiports,
    heliport_cells: HeliportCells,
    grid: HexGrid,
) -> BaseVertiports:
    """Keep the candidates whose cell exists and holds no heliport.

    Without this step the Rio de Janeiro data set yields no routes: one of the
    18 candidate droneports shares its cell with a heliport.
    """

    kept = []
    for point in candidates.points:
        cell = grid.get_cell_from_cartesian(point)
        if cell is None or cell.coord in heliport_cells.coords:
            continue
        kept.append(point)
    return BaseVertiports(points=tuple(kept))


def apply_vertiport_edits(
    base: BaseVertiports, edits: VertiportEdits, grid: HexGrid
) -> Vertiports:
    """Apply the edits in order to the base list.

    `add` appends the center of the cell; `remove` drops every vertiport
    whose cell is the edited one. The edits are validated before they are
    logged (see the intent handlers); this function does not check them.
    """

    points = list(base.points)
    for edit in edits.edits:
        if edit.kind == "add":
            points.append(grid.projection.cell_center(edit.coord))
        else:
            points = [
                point
                for point in points
                if (cell := grid.get_cell_from_cartesian(point)) is None
                or cell.coord != edit.coord
            ]
    return Vertiports(points=tuple(points))
