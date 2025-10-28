from abc import abstractmethod
from typing import List

from shapely import Point




class BaseClustering():
    """
    Abstract base class for all clustering algorithms in SkyWeaver.

    Provides a unified plotting interface and defines the core contract
    for implementing clustering logic and centroid computation.
    """

    # ==========================================================
    # Abstract Methods (to be implemented by subclasses)
    # ==========================================================

    @abstractmethod
    def fit(self, data: List[Point]):
        """Fit the clustering model to the data points."""
        pass

    @abstractmethod
    def predict(self, data: List[Point]) -> List[int]:
        """Predict the cluster labels for the given data points."""
        pass
