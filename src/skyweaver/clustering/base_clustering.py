from abc import abstractmethod
from typing import List

from shapely import Point
from skyweaver.clustering.logistics.cluster_outpost import ClusterOutpost



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
    def fit(self) -> ClusterOutpost:
        pass

    @abstractmethod
    def predict(self) -> List[int]:
        pass
