from typing import NamedTuple
import numpy as np


class Point(NamedTuple):
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        """Distância Euclidiana simples."""
        return np.hypot(self.x - other.x, self.y - other.y)
