from typing import Optional
import matplotlib.pyplot as plt
import numpy as np

from skyweaver.scenarios.distributions.distribution import Distribution

class BaseScenario:
    def __init__(self, distribution: Distribution, rng: Optional[np.random.Generator] = None):
        self.distribution = distribution
        self.rng = rng
        self.reset(rng)

    def reset(self, rng: Optional[np.random.Generator] = None):
        self.distribution.reset(rng)

    def plot(self):

        if self.distribution.config is None:
            raise ValueError(
                "Configuração não gerada. Chame reset() primeiro.")

        uav_pois = self.distribution.uav_pois
        mav_pois = self.distribution.mav_pois
        (x_min, x_max), (y_min, y_max) = self.distribution.domain

        plt.figure(figsize=(8, 8))
        plt.xlim(x_min, x_max)
        plt.ylim(y_min, y_max)

        if uav_pois:
            uav_xs, uav_ys = zip(*[(p.x, p.y) for p in uav_pois])
            plt.scatter(uav_xs, uav_ys, c='blue', label='UAV POIs')

        if mav_pois:
            mav_xs, mav_ys = zip(*[(p.x, p.y) for p in mav_pois])
            plt.scatter(mav_xs, mav_ys, c='red', label='MAV POIs')

        plt.title('UAV and MAV POI Distribution')
        plt.xlabel('X Coordinate')
        plt.ylabel('Y Coordinate')
        plt.legend()
        plt.grid()
        plt.show()
