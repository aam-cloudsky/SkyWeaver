from functools import cache
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.affinity import rotate as shp_rotate
from shapely.prepared import prep
from typing import Tuple, Iterable


class Stamp:
    """
    Rasterizes a local polygon (centered at 0,0) to a fixed, square grid.
    Rotation is applied around (0,0) with Shapely, and the mask is filled by
    shapely.contains on cell centers (no manual scanline).
    The grid is fixed (minx/miny and shape don't change with rotation), so
    the figure stays centered in the array for every angle.
    """

    def __init__(self, poly: Polygon, cell_size: float):
        # Expect a local polygon centered at (0,0)
        self.poly0: Polygon = poly
        self.cell_size: float = float(cell_size)

        # --- build a fixed, square support around origin ---
        # Maximum radius from origin to any exterior vertex
        coords = np.asarray(self.poly0.exterior.coords, dtype=float)
        rmax = np.sqrt((coords[:, 0] ** 2) + (coords[:, 1] ** 2)).max()

        # half-size in number of cells, add 1 cell margin
        half_cells = int(np.ceil(rmax / self.cell_size)) + 1

        # make grid size odd so the origin lies at the center of 4 pixels (rotation-friendly)
        self.nx = self.ny = 2 * half_cells + 1
        self.minx = -half_cells * self.cell_size
        self.miny = -half_cells * self.cell_size

        # cache key for the base polygon geometry (rotation is an argument later)
        # use a rounded tuple of coords to make it stable/hashable
        self._coords_key: Tuple[Tuple[float, float], ...] = tuple(
            (float(round(x, 6)), float(round(y, 6))) for x, y in self.poly0.exterior.coords
        )

    # -------------------------------
    # public API
    # -------------------------------
    def rotated_mask(self, angle_degree: int) -> np.ndarray:
        """
        Return a binary mask (ny, nx) for the polygon rotated by angle_degree.
        The support grid is fixed and centered at the origin, so the rotation
        does not translate the figure inside the mask.
        Results are cached per (coords_key, cell_size, nx, ny, minx/miny, angle_degree).
        """
        return Stamp._cached_rasterize(
            angle_degree,
            self.cell_size,
            self.nx,
            self.ny,
            self.minx,
            self.miny,
            self._coords_key,
        )

    # -------------------------------
    # cached core
    # -------------------------------
    @staticmethod
    @cache
    def _cached_rasterize(angle_degree: int,
                          cell_size: float,
                          nx: int, ny: int,
                          minx: float, miny: float,
                          coords_key: Tuple[Tuple[float, float], ...]) -> np.ndarray:
        """
        Cached rasterization using Shapely:
        - Rebuild polygon from coords_key
        - Rotate around (0,0) by angle_degree (degrees)
        - For each cell center, test contains() on the prepared geometry
        - Return uint8 mask (1 inside, 0 outside)
        """
        # rebuild & rotate
        poly0 = Polygon(coords_key)
        poly_rot = shp_rotate(poly0, angle_degree, origin=(0.0, 0.0), use_radians=False)
        prepped = prep(poly_rot)

        # cell-center coordinates
        xs = minx + (np.arange(nx) + 0.5) * cell_size
        ys = miny + (np.arange(ny) + 0.5) * cell_size

        mask = np.zeros((ny, nx), dtype=np.uint8)

        # Row-wise point tests (keeps Point() creations moderate)
        # Typical grids (e.g., radius ~2 km, cell 50 m) => ~81x81 points
        for iy, y in enumerate(ys):
            # build all points in this row
            row_points = [Point(x, y) for x in xs]
            inside = np.fromiter((prepped.contains(pt) for pt in row_points),
                                 dtype=bool, count=nx)
            mask[iy, inside] = 1

        return mask
