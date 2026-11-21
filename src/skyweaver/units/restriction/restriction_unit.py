from typing import Optional, Set

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.model.sites import Heliports
from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.restriction.logistics.restriction_outpost import RestrictionOutpost
from skyweaver.units.restriction.restrictions import locate_heliport_cells


class RestrictionUnit(OperationalUnit[RestrictionOutpost]):
    """
    Marks the heliport cells as restricted in the grid (old core only).

    The set of heliport cells comes from `locate_heliport_cells`; the marks
    are applied incrementally, as before.
    """

    def __init__(self, outpost: Optional[RestrictionOutpost] = None):
        super().__init__(outpost or RestrictionOutpost())

        self._prev_heliport_cells: Set[HexCell] = set()

    def run(self) -> None:
        grid = self._outpost.grid_parcel.grid
        heliports = Heliports(points=tuple(self._outpost.heliports_parcel.heliports))

        coords = locate_heliport_cells(heliports, grid).coords
        current_cells: Set[HexCell] = {
            cell
            for cell in (grid.get_cell_from_coord(coord) for coord in coords)
            if cell is not None
        }

        for cell in current_cells - self._prev_heliport_cells:
            cell.set_restricted()

        for cell in self._prev_heliport_cells - current_cells:
            cell.set_available()

        self._prev_heliport_cells = current_cells
