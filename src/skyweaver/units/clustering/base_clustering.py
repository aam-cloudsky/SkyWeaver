from abc import abstractmethod
from typing import List

from shapely.geometry import Point


class BaseClustering:
    """
    Abstract base class for all clustering algorithms in SkyWeaver.

    Provides a unified plotting interface and defines the core contract
    for implementing clustering logic and centroid computation.
    """

    # ==========================================================
    # Abstract Methods (to be implemented by subclasses)
    # ==========================================================

    @abstractmethod
    def fit_points(self, points: List[Point]) -> List[int]:
        pass
