

#from skyweaver.scenarios.base_scenario import BaseScenario
from typing import Optional

import numpy as np
from skyweaver.scenarios.base_scenario import BaseScenario
from skyweaver.scenarios.components.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution


class UAVMAVUAVScenario(BaseScenario):
    def __init__(self, rng: np.random.Generator):
        super().__init__(distribution=UAVMAVUAVDistribution(rng=rng), rng=rng)


if __name__ == "__main__":
    seed = 42
    rng = np.random.default_rng(seed)
    scenario = UAVMAVUAVScenario(rng)
    scenario.plot()