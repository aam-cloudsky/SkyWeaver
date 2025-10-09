# src/skyweaver/scenarios/components/voronoi/voronoi_cell.py

from dataclasses import dataclass
from typing import List
from skyweaver.core.geometry.point import Point


@dataclass
class VoronoiCell:
    label: str
    centroid: Point
    vertices: List[Point]
