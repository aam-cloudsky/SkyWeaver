

from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

from skyweaver.scenarios.components.distributions.distribution_configuration import DistributionConfiguration


class BaseDistribution(ABC):
    def __init__(self, config: DistributionConfiguration, rng: np.random.Generator):
        self._config: DistributionConfiguration = config
        self._rng = rng

    @property
    def domain(self) -> Tuple:
        return self._config.domain

    @property
    def uav_pois(self):
        return self._config.uav_points

    @property
    def mav_pois(self):
        return self._config.mav_points

    @property
    def config(self) -> DistributionConfiguration:
        return self._config

    @abstractmethod
    def reset(self, rng:Optional[np.random.Generator] = None):
        pass
