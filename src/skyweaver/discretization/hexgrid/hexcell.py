# src/skyweaver/tessellation/hexgrid/hexcell.py
from dataclasses import dataclass
from shapely.geometry import Polygon, Point
from typing import Tuple, Optional



class HexCell():
    center: Point