from dataclasses import dataclass
from typing import Tuple

from shapely.geometry import Point, Polygon
from functools import cache


@cache
def get_polygon(bound: "Bounds"):
    # This expensive operation only runs once for unique 'bound' arguments
    return Polygon(bound.corners)


@dataclass(frozen=True)
class Bounds:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @property
    def top_left(self) -> Point:
        return Point(self.min_x, self.max_y)

    @property
    def top_right(self) -> Point:
        return Point(self.max_x, self.max_y)

    @property
    def bottom_left(self) -> Point:
        return Point(self.min_x, self.min_y)

    @property
    def bottom_right(self) -> Point:
        return Point(self.max_x, self.min_y)

    def expand(self, margin: float) -> "Bounds":

        new_x_max = self.max_x + margin
        new_y_max = self.max_y + margin

        new_x_min = self.min_x - margin
        new_y_min = self.min_y - margin

        return Bounds.from_ranges(
            max_x=new_x_max, min_x=new_x_min, max_y=new_y_max, min_y=new_y_min
        )

    @property
    def corners(self) -> Tuple[Point, Point, Point, Point]:
        """
        Clockwise corners in local cartesian
        """
        return (self.top_left, self.top_right, self.bottom_right, self.bottom_left)

    def __hash__(self):
        _ROUND = 8  # Used only for hash operations
        return hash(
            tuple((round(p.x, _ROUND), round(p.y, _ROUND)) for p in self.corners)
        )

    def __eq__(self, other):
        if not isinstance(other, Bounds):
            return False
        return self.corners == other.corners

    @property
    def polygon(self) -> Polygon:
        return get_polygon(self)

    def contains(self, point: Point) -> bool:
        return (
            self.bottom_left.x <= point.x <= self.top_right.x
            and self.bottom_left.y <= point.y <= self.top_right.y
        )

    @staticmethod
    def empty():
        return Bounds.from_ranges(0, 0, 0, 0)

    @staticmethod
    def from_ranges(min_x, max_x, min_y, max_y) -> "Bounds":

        return Bounds(min_x=min_x, max_x=max_x, min_y=min_y, max_y=max_y)
