


from math import ceil, floor
from typing import List, Tuple
from skyweaver.discretization.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.hexgrid.hexgrid_configuration import HexGridConfiguration

from typing import Dict, Iterable
from skyweaver.discretization.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.hexgrid.hexcell import HexCell

from skyweaver.discretization.hexgrid.hexprojection import pixel_to_pointy_hex_frac, pointy_hex_to_pixel
from skyweaver.discretization.hexgrid.hextopology import neighbors
from skyweaver.discretization.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.hexgrid.hexcell import HexCell

class HexGrid:
    """
    Container for hexagonal cells indexed by HexCoord.
    Geometry and topology are handled by other modules.
    """

    def __init__(self):
        self._cells: Dict[HexCoord, HexCell] = {}

    # --- Basic container operations ----------------------------

    def add_cell(self, cell: HexCell) -> None:
        self._cells[cell.coord] = cell

    def remove_cell(self, coord: HexCoord) -> None:
        self._cells.pop(coord, None)

    def has_cell(self, coord: HexCoord) -> bool:
        return coord in self._cells

    def get_cell(self, coord: HexCoord) -> HexCell | None:
        return self._cells.get(coord)

    def cells(self) -> Iterable[HexCell]:
        return self._cells.values()

    def coords(self) -> Iterable[HexCoord]:
        return self._cells.keys()

    @classmethod
    def from_configuration(cls, config: HexGridConfiguration) -> "HexGrid":
        """
        Build a HexGrid covering the configured continuous domain.

        Invariant:
            HexCoord(0,0) <-> (0,0) in Euclidean space
        """
        grid = cls()

        (xmin, xmax), (ymin, ymax) = config.domain
        size = config.cell_size

        # 1. Fractional axial bounds
        corners = [
            pixel_to_pointy_hex_frac(xmin, ymin, size),
            pixel_to_pointy_hex_frac(xmin, ymax, size),
            pixel_to_pointy_hex_frac(xmax, ymin, size),
            pixel_to_pointy_hex_frac(xmax, ymax, size),
        ]

        q_vals = [c[0] for c in corners]
        r_vals = [c[1] for c in corners]

        q_min = floor(min(q_vals))
        q_max = ceil(max(q_vals))
        r_min = floor(min(r_vals))
        r_max = ceil(max(r_vals))

        # 2. Generate cells
        for q in range(q_min, q_max + 1):
            for r in range(r_min, r_max + 1):
                coord = HexCoord(q, r)
                x, y = pointy_hex_to_pixel(coord, size)

                if not cls._inside_domain(x, y, config.domain):
                    continue

                grid.add_cell(HexCell(coord=coord))

        return grid
    
    @staticmethod
    def _inside_domain(
        x: float,
        y: float,
        domain: tuple[tuple[float, float], tuple[float, float]],
    ) -> bool:
        (xmin, xmax), (ymin, ymax) = domain
        return xmin <= x <= xmax and ymin <= y <= ymax


    