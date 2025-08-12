import numpy as np
from typing import Dict, Tuple, List
from shapely import Point
from shapely.geometry import LineString, MultiLineString, Polygon, LineString
from shapely.prepared import prep


class Rasterizer:
    """
    Rasterizer class using the IDEAL (vector–raster hybrid) approach for spatial acceleration.
    Based on the paper “IDEAL: a Vector-Raster Hybrid Model for Efficient Spatial Queries
    over Complex Polygons” (MDM 2021) by Teng et al.  doi:10.1109/mdm52706.2021.00024

    The original implementation can be found in: https://github.com/StonyBrookDB/IDEAL/tree/master.
    I tried to adapt the idea for my problem. The general idea is to identify the borders, and fufill the interior.

    This class rasterizes a given Shapely polygon into a grid of cells based on a specified cell size.
    Each cell receives one of three status values:
      0 = exterior (outside the polygon),
      1 = border (intersects the polygon boundary),
      2 = interior (fully contained within the polygon).

    For border cells, the intersecting line segments are stored for further refinement if needed.

    The rasterization process consists of two main steps:
      1. Initial classification:
         - If the cell is fully within the polygon, mark as interior.
         - Else if the cell intersects the polygon boundary, mark as border, and save segments.
         - Else mark as exterior.

      2. Scanline fill:
         - For each row, toggles an 'in_region' flag each time a border cell is encountered.
         - Cells encountered while 'in_region' is True (and not already border) are marked interior.
         - This approximates filling the polygon interior following scanline rules.

    This structure allows:
      - O(1) checks for whether a point/cell is inside, outside, or on the boundary.
      - Reduction in shapely operations per cell, improving performance, especially in iterative loops.
    """

    def __init__(self, poly: Polygon, cell_size: float):
        self.poly = poly
        self.cell_size = cell_size
        self._setup_grid()

    def _setup_grid(self):
        minx, miny, maxx, maxy = self.poly.bounds
        self.nx = int(np.ceil((maxx - minx) / self.cell_size))
        self.ny = int(np.ceil((maxy - miny) / self.cell_size))
        self.minx, self.miny = minx, miny

        self.status = np.zeros((self.ny, self.nx), dtype=np.uint8)
        self.borders: Dict[
            Tuple[int, int], List[Tuple[Tuple[float, float], Tuple[float, float]]]
        ] = {}

        # Convert polygon exterior to list of edges
        coords = list(self.poly.exterior.coords)
        self.edges = [
            ((coords[i][0], coords[i][1]), (coords[i + 1][0], coords[i + 1][1]))
            for i in range(len(coords) - 1)
        ]

    @staticmethod
    def _segments_intersect(p1, p2, q1, q2) -> bool:
        """Check if segments p1-p2 and q1-q2 intersect."""

        def orient(a, b, c):
            return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

        o1 = orient(p1, p2, q1)
        o2 = orient(p1, p2, q2)
        o3 = orient(q1, q2, p1)
        o4 = orient(q1, q2, p2)
        return o1 * o2 < 0 and o3 * o4 < 0

    def partition(self):
        for iy in range(self.ny):
            in_region = False
            for ix in range(self.nx):
                # Cell bounds
                x0 = self.minx + ix * self.cell_size
                y0 = self.miny + iy * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size

                # Cell edges
                cell_edges = [
                    ((x0, y0), (x1, y0)),  # bottom
                    ((x1, y0), (x1, y1)),  # right
                    ((x1, y1), (x0, y1)),  # top
                    ((x0, y1), (x0, y0)),  # left
                ]

                # Test containment first (cheap)
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if self.poly.contains(Point(cx, cy)):
                    self.status[iy, ix] = 2
                    if not in_region:
                        in_region = True
                    continue

                # Check border by edge intersections
                border_segments = []
                for e1, e2 in self.edges:
                    for ce1, ce2 in cell_edges:
                        if self._segments_intersect(e1, e2, ce1, ce2):
                            border_segments.append((e1, e2))
                            break

                if border_segments:
                    self.status[iy, ix] = 1
                    self.borders[(iy, ix)] = border_segments
                    in_region = not in_region
                elif in_region:
                    self.status[iy, ix] = 2

        return self.status
