# src/skyweaver/units/distributions/base_distribution.py

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import numpy as np
from shapely.geometry import Point


class BaseDistribution(ABC):
    """A generator of UAV and MAV points of interest inside a rectangular domain.

    The generated points are kept on the instance (`domain`, `uav_pois`,
    `mav_pois`); before the migration to Reed they were written to the old
    core's depot through a DistributionOutpost.
    """

    def __init__(self, rng: np.random.Generator):
        self._rng = rng
        self._domain: Tuple = ()
        self._uav_pois: List[Point] = []
        self._mav_pois: List[Point] = []

    @property
    def domain(self) -> Tuple:
        return self._domain

    @property
    def uav_pois(self) -> List[Point]:
        return self._uav_pois

    @property
    def mav_pois(self) -> List[Point]:
        return self._mav_pois

    @abstractmethod
    def reset(self, rng: Optional[np.random.Generator] = None):
        pass

    @abstractmethod
    def generate_points(self):
        pass
