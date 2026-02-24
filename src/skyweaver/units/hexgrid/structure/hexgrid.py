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
        orientation: HexOrientation = HexOrientation.POINTY,
        operational_bounds: Bounds = Bounds(0, 10, 0, 10),
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
        if not self.coord_inside_domain(coord):
            return None

        cell = self._cells.get(coord)
        if cell is None:
            cell = self._create_cell(coord)

        return cell

    # TODO: BETTER NAMING FOR GET CELLS
    # accept only point as location
    def get_cell(self, cartesian: Point) -> Optional[HexCell]:
        coord = self.projection.pixel_to_pointy_hex(cartesian.x, cartesian.y)

        return self.get_cell_from_coord(coord)

    def get_cell_from_cartesian(self, x: float, y: float) -> Optional[HexCell]:
        coord = self.projection.pixel_to_pointy_hex(x, y)

        return self.get_cell_from_coord(coord)

    def get_cell_from_cartesians(self, points: Iterable[Point]) -> List[HexCell]:
        cells: list[HexCell] = []
        for point in points:
            cell = self.get_cell_from_cartesian(point.x, point.y)
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

    def coord_inside_domain(
        self,
        coord: HexCoord,
    ) -> bool:
        x, y = self.projection.pointy_hex_to_pixel(coord)
        xmin, xmax = self._domain_bounds.min_x, self._domain_bounds.max_x
        ymin, ymax = self._domain_bounds.min_y, self._domain_bounds.max_y
        return xmin <= x <= xmax and ymin <= y <= ymax

    def cartesian_cell_center(self, cell: HexCell) -> Point:
        return self.projection.cell_center(cell.coord)

    def cell_polygon(self, cell: HexCell) -> Polygon:
        return self.projection.cell_polygon(cell.coord)

    # =======================================================
    # Static Methods
    # =======================================================

    @staticmethod
    def inside_domain(
        x: float,
        y: float,
        bounds: Bounds,
    ) -> bool:
        xmin, xmax = bounds.min_x, bounds.max_x
        ymin, ymax = bounds.min_y, bounds.max_y
        return xmin <= x <= xmax and ymin <= y <= ymax
