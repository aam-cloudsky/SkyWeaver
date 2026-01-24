# src/skyweaver/distributions/base_distribution.py

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np

from skyweaver.distributions.distribution_outpost import DistributionOutpost


class BaseDistribution(ABC):
    def __init__(self, rng: np.random.Generator):
        # 🔑 Cada Distribution tem sua própria view reativa
        self._depot_outpost: DistributionOutpost = DistributionOutpost()
        self._rng = rng

    @property
    def domain(self) -> Tuple:
        return self._depot_outpost.airspace_points.domain

    @property
    def uav_pois(self):
        return self._depot_outpost.airspace_points.uav_points

    @property
    def mav_pois(self):
        return self._depot_outpost.airspace_points.mav_points
    
    @property
    def outpost(self) -> DistributionOutpost:
        return self._depot_outpost

    @abstractmethod
    def reset(self, rng: Optional[np.random.Generator] = None):
        pass

    @abstractmethod
    def generate_points(self):
        pass
