from math import ceil, floor
from typing import List, Optional, Tuple

from shapely.geometry import Point, Polygon


from typing import Dict, Iterable

from typing import Dict

from skyweaver.units.domain.frame.bounds import Bounds
from skyweaver.units.hexgrid.geometry.hex_orientation import HexOrientation
from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord

from skyweaver.units.hexgrid.geometry.hexprojection import HexProjection
from skyweaver.units.hexgrid.geometry.hextopology import HexTopology


class HexGrid:
    """
    Container for hexagonal cells indexed by HexCoord.
    Geometry and topology are handled by other modules.
    """

    def __init__(
        self,
        cell_size: float = 1.0,
        operational_bounds: Bounds = Bounds.empty(),
        orientation: HexOrientation = HexOrientation.POINTY,
    ):

        self._cells: Dict[HexCoord, HexCell] = {}

        self.projection = HexProjection(size=cell_size, orientation=orientation)
        self.topology = HexTopology()
        self._domain_bounds = operational_bounds

        self._cell_size: float = cell_size

    # =======================================================
    # Private Functions
    # =======================================================

    def _create_cell(self, coord: HexCoord) -> HexCell:
        cell = HexCell(coord=coord, size=self._cell_size)

        self._cells[coord] = cell
        return cell

    # =======================================================
    # Public Functions
    # =======================================================

    def domain_bounds(self) -> Bounds:
        return self._domain_bounds

    def get_cell_from_coord(self, coord: HexCoord) -> Optional[HexCell]:
        if not self.contains_hexcoord(coord):
            return None

        cell = self._cells.get(coord)
        if cell is None:
            cell = self._create_cell(coord)

        return cell

    def get_cell_from_cartesian(self, local: Point) -> Optional[HexCell]:
        coord = self.projection.cartesian_to_pointy_hex(local)

        return self.get_cell_from_coord(coord)

    def get_cell_from_cartesians(self, points: Iterable[Point]) -> List[HexCell]:
        cells: list[HexCell] = []
        for point in points:
            cell = self.get_cell_from_cartesian(point)
            if cell is not None:
                cells.append(cell)

        return cells

    def iter_domain_cells(self) -> Iterable[HexCell]:
        """
        Lazily iterate over all hex cells inside the domain.

        Cells are created on-demand during iteration.
        Intended for debugging / visualization only.
        """

        bounds = self._domain_bounds
        axial_bounds = self.projection.axial_bounds_from_cartesian_bounds(bounds)

        for coord in axial_bounds.iter_coords():
            cell = self.get_cell_from_coord(coord)
            if cell is not None:
                yield cell

    def neighbors(self, cell: HexCell) -> List[HexCell]:
        coords = self.topology.neighbors(cell.coord)

        neighborhood: list[HexCell] = []
        for c in coords:
            nb = self.get_cell_from_coord(c)
            if nb is not None:
                neighborhood.append(nb)

        return neighborhood

    def lower_bound_steps(self, a: HexCell, b: HexCell) -> float:
        """Estimate the minimum number of steps between two cells"""
        min_distance: int = self.topology.hex_distance(a.coord, b.coord)
        return min_distance  # Default implementation; override in subclasses

    def cartesian_cell_center(self, cell: HexCell) -> Point:
        """
        Local coordnate system

        """
        return self.projection.cell_center(cell.coord)

    def cell_polygon(self, cell: HexCell) -> Polygon:
        """
        Local coordnate system

        """
        return self.projection.cell_polygon(cell.coord)

    # =======================================================
    # Contains functions
    # =======================================================

    def contains_cartesian(self, local: Point) -> bool:
        return self._domain_bounds.contains(local)

    def contains_hexcoord(self, coord: HexCoord) -> bool:
        cartesian = self.projection.pointy_hex_to_cartesian(coord)
        return self.contains_cartesian(cartesian)

    def contains_cell(self, cell: HexCell) -> bool:
        return self.contains_hexcoord(cell.coord)
