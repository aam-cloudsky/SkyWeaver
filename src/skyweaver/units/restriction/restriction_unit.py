from typing import List, Optional, Set

from shapely.geometry import Point

from skyweaver.core.operations.operational_unit import OperationalUnit

from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.restriction.logistics.restriction_outpost import RestrictionOutpost


class RestrictionUnit(OperationalUnit[RestrictionOutpost]):
    """
    Applies hard constraints incrementally.

    - No rollback
    - No full-grid reset
    - Updates only delta
    - Cache lives inside unit (Option A)
    """

    def __init__(self, outpost: Optional[RestrictionOutpost] = None):
        super().__init__(outpost or RestrictionOutpost())

        # Local incremental cache
        self._prev_heliport_cells: Set[HexCell] = set()

    def run(self) -> None:
        heliports: List[Point] = self._outpost.heliports_parcel.heliports
        grid: HexGrid = self._outpost.grid_parcel.grid

        # 1️⃣ Compute current heliport cells
        current_cells: Set[HexCell] = self._resolve_cells(heliports, grid)

        # 2️⃣ Compute delta
        added = current_cells - self._prev_heliport_cells
        removed = self._prev_heliport_cells - current_cells

        # 3️⃣ Apply only what changed
        for cell in added:
            cell.set_restricted()

        for cell in removed:
            cell.set_available()

        # 4️⃣ Update cache
        self._prev_heliport_cells = current_cells

    def _resolve_cells(self, points: List[Point], grid: HexGrid) -> Set[HexCell]:
        cells: Set[HexCell] = set()

        for point in points:
            cell: Optional[HexCell] = grid.get_cell(cartesian=point)
            if cell is not None:
                cells.add(cell)

        return cells
