# src/skyweaver/tessellation/hexgrid/hexcell.py
from dataclasses import dataclass
from shapely.geometry import Polygon, Point
from typing import Tuple, Optional

from skyweaver.discretization.hexgrid.hexcoord import HexCoord


@dataclass
class HexCell():
    """
    This HexCell represents a single hexagonal cell in a hexagonal grid.
    It is defined by its Hex Coordinates (Axial Coordinates), size (distance from center to any vertex),
    
    """

    coord: HexCoord  # Forward reference to HexCoord
    navigable: bool = True
    cost: float = 1.0
    
    
