from dataclasses import dataclass


@dataclass(frozen=True)
class Bounds:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    @staticmethod
    def empty():
        return Bounds(0, 0, 0, 0)
