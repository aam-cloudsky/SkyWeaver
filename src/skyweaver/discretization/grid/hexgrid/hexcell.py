# src/skyweaver/tessellation/hexgrid/hexcell.py
from dataclasses import dataclass, field
from shapely.geometry import Polygon, Point
from typing import Tuple

from skyweaver.discretization.grid.base_cell import BaseCell
from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord

import math


from skyweaver.discretization.grid.hexgrid.hexprojection import pointy_hex_to_pixel

@dataclass
class HexCell(BaseCell):
    """
    This HexCell represents a single hexagonal cell in a hexagonal grid.
    It is defined by its Hex Coordinates (Axial Coordinates), size (distance from center to any vertex),
    
    """

    coord: HexCoord  # Forward reference to HexCoord
    _size: float  # Distance from center to any vertex
    _cost: float = 1.0
    _navigable: bool = field(init=False)
    _polygon: Polygon = field(init=False)
    _cartesian_center: Point = field(init=False)

    @property
    def polygon(self) -> Polygon:
        """Return the shapely Polygon representing the hex cell in 2D space."""
        if not hasattr(self, '_polygon'):
            self._polygon = self._create_polygon()
        return self._polygon
    
    def _create_polygon(self):
        """
            Creates a regular hexagon polygon based on the cell's axial coordinates and size, with a pointy-top orientation.
        """
        cx, cy = pointy_hex_to_pixel(self.coord, self.size)
        vertices = []

        for i in range(6):
            angle_rad = math.radians(60 * i + 30)  # pointy-top correction
            x = cx + self.size * math.cos(angle_rad)
            y = cy + self.size * math.sin(angle_rad)
            vertices.append((x, y))

        return Polygon(vertices)

    
    @property
    def cartesian_center(self) -> Point:
        """Return the (x, y) coordinates of the hex cell center."""
        if not hasattr(self, '_cartesian_center'):
            self._cartesian_center = Point(pointy_hex_to_pixel(self.coord, self.size))
        return self._cartesian_center
    
    @property
    def cost(self) -> float:
        return self._cost

    @property
    def navigable(self) -> bool:
        return self._navigable

    @navigable.setter
    def navigable(self, value: bool) -> None:
        self._navigable = value


    @property
    def size(self) -> float:
        return self._size