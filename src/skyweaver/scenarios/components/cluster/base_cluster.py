from abc import ABC, abstractmethod
from typing import List
from skyweaver.core.geometry.point import Point
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from skyweaver.scenarios.components.cluster.cluster_boundary import ClusterBoundary
from skyweaver.scenarios.components.cluster.cluster_configuration import ClusterConfiguration


from shapely.geometry import LineString, Polygon, Point as ShapelyPoint
from shapely.ops import unary_union
from scipy.interpolate import UnivariateSpline
import numpy as np
import hdbscan
import matplotlib.pyplot as plt
from sklearn.metrics import davies_bouldin_score
from typing import Dict, List, Any

from skyweaver.core.geometry.point import Point



class BaseCluster():
    """
    Abstract base class for all clustering algorithms in SkyWeaver.

    Provides a unified plotting interface and defines the core contract
    for implementing clustering logic and centroid computation.
    """


    def __init__(self):
        self.cluster_boundary = ClusterBoundary()
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
