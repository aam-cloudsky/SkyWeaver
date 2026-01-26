# src/skyweaver/tessellation/hexgrid/hexcell.py

import math
from shapely.geometry import Polygon, Point
from skyweaver.discretization.grid.base_cell import BaseCell
from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.grid.hexgrid.hexprojection import pointy_hex_to_pixel



class HexCell(BaseCell):
    """
    This HexCell represents a single hexagonal cell in a hexagonal grid.
    It is defined by its Hex Coordinates (Axial Coordinates), size (distance from center to any vertex),
    
    """

    def __init__(self, coord: HexCoord, size: float, cost: float = 1.0, available: bool = True):
        super().__init__(size=size, cost=cost, available=available)
        self._coord: HexCoord = coord

    @property 
    def coord(self) -> HexCoord: 
        return self._coord

    def _create_polygon(self):
        """
            Creates a regular hexagon polygon based on the cell's axial coordinates and size, with a pointy-top orientation.
        """
        cx, cy = pointy_hex_to_pixel(self._coord, self._size)
        vertices = []

        for i in range(6):
            angle_rad = math.radians(60 * i + 30)  # pointy-top correction
            x = cx + self.size * math.cos(angle_rad)
            y = cy + self.size * math.sin(angle_rad)
            vertices.append((x, y))

        return Polygon(vertices)


    def _compute_cartesian_center(self) -> Point:
        """Return the (x, y) coordinates of the hex cell center."""

        return Point(pointy_hex_to_pixel(self._coord, self._size))
        
    def __eq__(self, other):
        if not isinstance(other, HexCell):
            return NotImplemented
        return (
            self._coord == other._coord
            and self._size == other._size
        )

    def __hash__(self):
        return hash((self._coord, self._size))

    