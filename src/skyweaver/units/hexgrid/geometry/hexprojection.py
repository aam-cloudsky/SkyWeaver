from math import ceil, floor
import math
from typing import Tuple

from shapely.geometry import Point, Polygon

from skyweaver.units.domain.frame.bounds import Bounds
from skyweaver.units.hexgrid.geometry.axial_bounds import AxialBounds
from skyweaver.units.hexgrid.geometry.hex_orientation import HexOrientation
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord


class HexProjection:

    def __init__(self, size: float, orientation: HexOrientation):
        if orientation != HexOrientation.POINTY:
            raise NotImplementedError(
                "[HexProjection] Only pointy-top hexagons are currently supported."
            )

        self.size = size
        self.orientation = orientation

    @classmethod
    def lerp(cls, a: HexCoord, b: HexCoord, t: float) -> tuple[float, float]:
        """ "
        Linear interpolation between two hex coordinates a and b, where t is a parameter between 0 and 1.
        This is used for smooth transitions and animations between hex cells.
        The function calculates the difference between the two coordinates, scales it by t,
        and adds it to the starting coordinate a to get the interpolated coordinates.
        The result is returned as a tuple of (q, r) which are the axial coordinates of the interpolated position.
        """
        diff = b - a
        q = a.q + diff.q * t
        r = a.r + diff.r * t
        return q, r

    @classmethod
    def hex_round(cls, q_frac: float, r_frac: float) -> HexCoord:
        """
        Rounds fractional axial coordinates to the nearest hex cell.
        This is necessary because converting from pixel to hex coordinates can yield fractional values.

            -  Notice that hex coord must keep a constraint: q + r + s = 0, where s is the third coordinate in cube coordinates.
            -  The rounding process involves rounding q, r, and s to the nearest integers,
            and then adjusting the one with the largest rounding difference to ensure the constraint is maintained.
        """

        s_frac = -q_frac - r_frac
        rq, rr, rs = round(q_frac), round(r_frac), round(s_frac)

        # Compute biggest rounding difference
        dq: float = abs(rq - q_frac)
        dr: float = abs(rr - r_frac)
        ds: float = abs(rs - s_frac)

        # use the largest difference to adjust the rounded coordinates to ensure q + r + s = 0
        if cls._is_error_q_highest(dq, dr, ds):
            # forget round of q, and compute it from r and s to maintain the constraint
            rq = -rr - rs
        elif cls._is_error_r_higher_than_s(dr, ds):
            # forget round of r, and compute it from q and s to maintain the constraint
            rr = -rq - rs

        return HexCoord(rq, rr)

    @classmethod
    def _is_error_q_highest(cls, dq: float, dr: float, ds: float) -> bool:
        return dq > dr and dq > ds

    @classmethod
    def _is_error_r_higher_than_s(cls, dr: float, ds: float) -> bool:
        return dr > ds

    @classmethod
    def hex_sample(cls, a: HexCoord, b: HexCoord, t: float) -> HexCoord:
        q, r = cls.lerp(a, b, t)
        return cls.hex_round(q, r)

    def pointy_hex_to_pixel(self, hex: HexCoord) -> Tuple[float, float]:
        size: float = self.size
        x = (3**0.5) * hex.q + ((3**0.5) * hex.r / 2)
        y = 3 / 2 * hex.r
        return size * x, size * y

    def pixel_to_pointy_hex(self, x: float, y: float) -> HexCoord:
        size: float = self.size
        q = ((3**0.5) / 3 * x - (1 / 3) * y) / size
        r = (2 / 3 * y) / size
        return self.hex_round(q, r)

    def pixel_to_pointy_hex_frac(self, x: float, y: float) -> tuple[float, float]:
        size = self.size
        q = ((3**0.5) / 3 * x - (1 / 3) * y) / size
        r = (2 / 3 * y) / size

        return q, r

    def axial_bounds_from_cartesian_bounds(self, bounds: Bounds) -> AxialBounds:
        corners = [
            self.pixel_to_pointy_hex_frac(bounds.min_x, bounds.min_y),
            self.pixel_to_pointy_hex_frac(bounds.min_x, bounds.max_y),
            self.pixel_to_pointy_hex_frac(bounds.max_x, bounds.min_y),
            self.pixel_to_pointy_hex_frac(bounds.max_x, bounds.max_y),
        ]

        q_vals = [c[0] for c in corners]
        r_vals = [c[1] for c in corners]

        min_q: int = int(floor(min(q_vals)))
        max_q: int = int(ceil(max(q_vals)))
        min_r: int = int(floor(min(r_vals)))
        max_r: int = int(ceil(max(r_vals)))

        return AxialBounds(min_q=min_q, max_q=max_q, min_r=min_r, max_r=max_r)

    def cell_center(self, coord: HexCoord) -> Point:
        x, y = self.pointy_hex_to_pixel(coord)
        return Point(x, y)

    def cell_polygon(self, coord: HexCoord) -> Polygon:
        cx, cy = self.pointy_hex_to_pixel(coord)

        vertices = []
        for i in range(6):
            angle_rad = math.radians(60 * i + 30)
            x = cx + self.size * math.cos(angle_rad)
            y = cy + self.size * math.sin(angle_rad)
            vertices.append((x, y))

        return Polygon(vertices)
