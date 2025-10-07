
from typing import Optional
import numpy as np

from skyweaver.scenarios.distributions.components.configuration import DistributionConfiguration
from skyweaver.scenarios.distributions.components.point import Point
from skyweaver.scenarios.distributions.distribution import Distribution


class UAVMAVUAVDistribution(Distribution):
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
        
        _config = self._setup_config(n_uav, n_mav, domain, center_fraction, rng)
        super().__init__(config=_config, rng=rng)

    def reset(self, rng: Optional[np.random.Generator] = None):
        """Reinicializa o gerador aleatório e recria a configuração."""
        if rng is not None:
            self._rng = rng
        self._config = self._setup_config(
            self._n_uav, self._n_mav, self._domain, self._center_fraction, self._rng
        )


    def _setup_config(self, _n_uav, _n_mav, _domain, _center_fraction, rng) -> DistributionConfiguration:
        """Gera os POIs e armazena no DistributionConfig."""
        uavs = self.generate_uav_pois(_n_uav, _domain, rng)
        mavs = self.generate_mav_pois(_n_mav, _domain, _center_fraction, rng)

        return DistributionConfiguration(
            domain=_domain,
            poi_uav=uavs,
            poi_mav=mavs,
        )

    # --------------------------------------------------
    # Geradores de POIs
    # --------------------------------------------------

    def generate_uav_pois(
        self, n_poi: int, domain: tuple, rng: np.random.Generator
    ) -> tuple[Point, ...]:
        """Gera UAV POIs nas extremidades, concentrados em torno de centros aleatórios."""
        (x_min, x_max), (y_min, y_max) = domain
        half = n_poi // 2

        # Domínio e dispersão relativos
        x_span = x_max - x_min
        y_span = y_max - y_min

        # Dispersão controlada (clusters mais compactos)
        x_sigma = 0.05 * x_span  # 5% da largura → mais concentrado
        y_sigma = 0.10 * y_span  # 10% da altura

        # 🔹 Faixa segura para os centros (10% afastado das bordas)
        margin_x = 0.10 * x_span
        left_center_x = rng.uniform(x_min + margin_x, x_min + 0.25 * x_span)
        right_center_x = rng.uniform(x_max - 0.25 * x_span, x_max - margin_x)

        # Centros em Y também levemente aleatórios, mas não muito próximos das bordas
        center_y_left = rng.uniform(y_min + 0.25 * y_span, y_max - 0.25 * y_span)
        center_y_right = rng.uniform(y_min + 0.25 * y_span, y_max - 0.25 * y_span)

        # Gera pontos normais ao redor dos centros
        uav_left = np.c_[
            rng.normal(left_center_x, x_sigma, half),
            rng.normal(center_y_left, y_sigma, half),
        ]
        uav_right = np.c_[
            rng.normal(right_center_x, x_sigma, half),
            rng.normal(center_y_right, y_sigma, half),
        ]

        # Clippa suavemente
        uavs = np.vstack([uav_left, uav_right])
        uavs[:, 0] = np.clip(uavs[:, 0], x_min + margin_x /
                            2, x_max - margin_x / 2)
        uavs[:, 1] = np.clip(uavs[:, 1], y_min, y_max)

        return tuple(Point(x, y) for x, y in uavs)


    def generate_mav_pois(
        self,
        n_poi: int,
        domain: tuple,
        center_fraction: float,
        rng: np.random.Generator,
    ) -> tuple[Point, ...]:
        """Gera MAV POIs concentrados no centro, mas com alongamento vertical (em Y)."""
        (x_min, x_max), (y_min, y_max) = domain
        x_span = x_max - x_min
        y_span = y_max - y_min

        # Centro aleatório dentro da zona central
        x_center = rng.uniform(-x_span * center_fraction /
                            2, x_span * center_fraction / 2)
        y_center = rng.uniform(-y_span * 0.1, y_span * 0.1)

        # Dispersão diferente nos eixos (alongado em Y)
        x_sigma = 0.05 * x_span  # 5% da largura
        y_sigma = 0.25 * y_span  # 25% da altura

        mavs = np.c_[
            rng.normal(x_center, x_sigma, n_poi),
            rng.normal(y_center, y_sigma, n_poi),
        ]

        mavs[:, 0] = np.clip(mavs[:, 0], x_min, x_max)
        mavs[:, 1] = np.clip(mavs[:, 1], y_min, y_max)

        return tuple(Point(x, y) for x, y in mavs)
