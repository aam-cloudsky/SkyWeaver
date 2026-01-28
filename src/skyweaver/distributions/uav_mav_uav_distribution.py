from typing import Optional
import numpy as np
from shapely.geometry import Point

from skyweaver.distributions.base_distribution import BaseDistribution
from skyweaver.distributions.logistics.distribution_outpost import DistributionOutpost


class UAVMAVUAVDistribution(BaseDistribution):
    """
    Cenário: UAVs nas extremidades (esquerda e direita)
    e MAVs concentrados na região central.

    O domínio é um retângulo 2D definido por ((x_min, x_max), (y_min, y_max)).
    """

    def __init__(
        self,
        rng: np.random.Generator,
        n_uav: int = 20,
        n_mav: int = 10,
        domain: tuple = ((-1000, 1000), (-1000, 1000)),
        center_fraction: float = 0.3,
    ):
        self._n_uav = n_uav
        self._n_mav = n_mav
        self._domain = domain
        self._center_fraction = center_fraction
        self._rng = rng

        # BaseDistribution agora cria sua própria view do Depot
        super().__init__(rng=rng)

        # Gera e escreve no Depot
        self.generate_points()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, rng: Optional[np.random.Generator] = None):
        """Reinicializa o gerador aleatório e recria a configuração."""
        if rng is not None:
            self._rng = rng
        self.generate_points()

    def generate_points(self):
        """Gera os pontos UAV e MAV e escreve no Depot."""
        uav_points = self.generate_uav_pois(
            self._n_uav, self._domain, self._rng
        )
        mav_points = self.generate_mav_pois(
            self._n_mav, self._domain, self._center_fraction, self._rng
        )

        print(f"Generated {len(uav_points)} UAV points and {len(mav_points)} MAV points.")
        # 🔑 Escrita correta: via Outpost → Depot
        with DistributionOutpost() as outpost:
            ap = outpost.airspace_points
            ap.domain = self._domain
            ap.uav_points = uav_points
            ap.mav_points = mav_points

        print(f"{DistributionOutpost().airspace_points.uav_points}")

    # --------------------------------------------------
    # Geradores de POIs
    # --------------------------------------------------

    def generate_uav_pois(
        self, n_poi: int, domain: tuple, rng: np.random.Generator
    ) -> list[Point]:
        """Gera UAV POIs nas extremidades."""
        (x_min, x_max), (y_min, y_max) = domain
        half = n_poi // 2

        x_span = x_max - x_min
        y_span = y_max - y_min

        x_sigma = 0.05 * x_span
        y_sigma = 0.10 * y_span

        margin_x = 0.10 * x_span
        left_center_x = rng.uniform(x_min + margin_x, x_min + 0.25 * x_span)
        right_center_x = rng.uniform(x_max - 0.25 * x_span, x_max - margin_x)

        center_y_left = rng.uniform(
            y_min + 0.25 * y_span, y_max - 0.25 * y_span)
        center_y_right = rng.uniform(
            y_min + 0.25 * y_span, y_max - 0.25 * y_span)

        uav_left = np.c_[
            rng.normal(left_center_x, x_sigma, half),
            rng.normal(center_y_left, y_sigma, half),
        ]
        uav_right = np.c_[
            rng.normal(right_center_x, x_sigma, half),
            rng.normal(center_y_right, y_sigma, half),
        ]

        uavs = np.vstack([uav_left, uav_right])
        uavs[:, 0] = np.clip(uavs[:, 0], x_min +
                             margin_x / 2, x_max - margin_x / 2)
        uavs[:, 1] = np.clip(uavs[:, 1], y_min, y_max)

        return [Point(x, y) for x, y in uavs]

    def generate_mav_pois(
        self,
        n_poi: int,
        domain: tuple,
        center_fraction: float,
        rng: np.random.Generator,
    ) -> list[Point]:
        """Gera MAV POIs concentrados no centro."""
        (x_min, x_max), (y_min, y_max) = domain
        x_span = x_max - x_min
        y_span = y_max - y_min

        x_center = rng.uniform(
            -x_span * center_fraction / 2,
            x_span * center_fraction / 2,
        )
        y_center = rng.uniform(-y_span * 0.1, y_span * 0.1)

        x_sigma = 0.05 * x_span
        y_sigma = 0.25 * y_span

        mavs = np.c_[
            rng.normal(x_center, x_sigma, n_poi),
            rng.normal(y_center, y_sigma, n_poi),
        ]

        mavs[:, 0] = np.clip(mavs[:, 0], x_min, x_max)
        mavs[:, 1] = np.clip(mavs[:, 1], y_min, y_max)

        return [Point(x, y) for x, y in mavs]


