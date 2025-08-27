from affine import Affine
from shapely.geometry import Polygon
from functools import cache
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.affinity import rotate as shp_rotate
from shapely.affinity import translate as shp_translate
from shapely.prepared import prep
from typing import Tuple, Iterable
from rasterio import features
#from skyweaver.managers.components.stamp import Stamp
from functools import cache
from shapely import Point, Polygon

import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple

from skyweaver.data_models.restriction import Restriction
from skyweaver.enums.shapes import RestrictionShape




class Stamp:
    """
    Rasterizes a local polygon (centered at 0,0) to a fixed, square grid.
    Rotation is applied around (0,0) with Shapely, and the mask is filled by
    shapely.contains on cell centers (no manual scanline).
    The grid is fixed (minx/miny and shape don't change with rotation), so
    the figure stays centered in the array for every angle.
    """

    
    
    #=================================================================================
    # Polygon Generation
    #=================================================================================

    @staticmethod
    @cache
    def _retrieve_polygon(shape: RestrictionShape, radius: int) -> Polygon:
        """
        Returns the polygon representation of the restriction shape.
        """
        if shape == RestrictionShape.DISK:
            return Stamp._disk_polygon(radius=radius)
        elif shape == RestrictionShape.RECTANGLE:
            return Stamp._rectangle_polygon(radius=radius)
        elif shape == RestrictionShape.CIRCULAR_SECTOR:
            return Stamp._circular_sector_polygon(radius=radius)
        else:
            raise ValueError(f"Unsupported shape: {shape.name}")



    @staticmethod
    @cache
    def _disk_polygon(radius: int) -> Polygon:
        """
        Returns a circular polygon with the specified radius.
        """
        return Point(0, 0).buffer(radius, resolution=32)

    @staticmethod
    @cache
    def _rectangle_polygon(radius: int) -> Polygon:
        # radius is diagonal length, so half side is radius / sqrt(2)
        half_side = radius / np.sqrt(2)
        return Polygon(
            [
                (-half_side, -half_side),
                (+half_side, -half_side),
                (+half_side, +half_side),
                (-half_side, +half_side),
            ]
        )

    @staticmethod
    @cache
    def _circular_sector_polygon(
        radius: int, angle_rad: float = (2 / 3) * np.pi
    ) -> Polygon:
        """
        Return a triangular polygon that approximates the circular sector.

        - Height: self.radius
        - Angle: angle_rad (default 120 degrees)
        """

        # ponto do vértice (no centro)
        apex = (0.0, 0.0)

        # ângulos para os dois cantos da base
        half_angle = angle_rad / 2.0

        # coordenadas dos vértices da base (distância = raio)
        p1 = (
            radius * np.cos(half_angle),
            radius * np.sin(half_angle),
        )
        p2 = (
            radius * np.cos(-half_angle),
            radius * np.sin(-half_angle),
        )

        # triângulo formado: ápice + dois pontos da base
        return Polygon([apex, p1, p2])
    
    @staticmethod
    @cache
    def _rotated_polygon_degree(shape: RestrictionShape, radius: int, degree: int) -> Polygon:
        base = Stamp._retrieve_polygon(shape, radius)
        return shp_rotate(base, degree, origin=(0.0, 0.0), use_radians=False)
    
    #=================================================================================
    # Rasterization
    #=================================================================================

    @staticmethod
    @cache
    def _grid_signature(shape: RestrictionShape, radius: int, cell_size: int):
        poly = Stamp._retrieve_polygon(shape, radius)
        coords = np.asarray(poly.exterior.coords, dtype=float)
        rmax = np.sqrt((coords[:, 0] ** 2) + (coords[:, 1] ** 2)).max()
        half_cells = int(np.ceil(rmax / cell_size)) + 1
        nx = ny = 2 * half_cells + 1
        minx = -half_cells * cell_size
        miny = -half_cells * cell_size
        return nx, ny, minx, miny

    
    @cache
    @staticmethod
    def _to_cell_mask(geometry_signature: Tuple, cell_size: int):
        shape, radius, degree = geometry_signature

        rotated_polygon = Stamp._rotated_polygon_degree(shape, radius, degree)
        nx, ny, minx, miny = Stamp._grid_signature(shape, radius, cell_size)


        # Define transform for rasterio
        transform = Affine(cell_size, 0, minx, 0, -cell_size, miny + ny * cell_size)

        # Rasterize directly
        mask = features.rasterize(
            [(rotated_polygon, 1)],
            out_shape=(ny, nx),
            transform=transform,
            fill=0,
            all_touched=False, 
            dtype='uint8'
        )

        return mask
    
    @staticmethod
    def to_cell_mask(restriction: Restriction, cell_size: int) -> np.ndarray:
        """
        Returns the rasterized mask of the restriction at its current rotation.
        Uses cached Stamp to avoid recomputing the base polygon.
        """

        geometry_signature = restriction.geometry_signature
        return Stamp._to_cell_mask(geometry_signature, cell_size)

    
    @staticmethod
    def to_world_polygon(restriction: Restriction) -> Polygon:
        """
        Return the restriction polygon in world coordinates:
        - Starts from the cached local polygon (centered at 0,0).
        - Applies exact rotation (in radians).
        - Translates to restriction.location.
        """
        polygon = Stamp._retrieve_polygon(restriction.shape, restriction.radius)
        rotated = shp_rotate(polygon, restriction.rotation, origin=(0.0, 0.0), use_radians=True)
        return shp_translate(rotated, xoff=restriction.location.x, yoff=restriction.location.y)



    #=================================================================================
    # Metrics
    #=================================================================================

    @staticmethod
    def occupation_in_cells(restriction: Restriction, cell_size: int) -> int:
        """
        Returns the number of occupied cells.
        """

        mask = Stamp.to_cell_mask(restriction, cell_size)
        return int(np.count_nonzero(mask))

    
