# src/skyweaver/scenarios/components/voronoi/voronoi_configuration.py

from typing import List, Dict
from skyweaver.core.geometry.point import Point
from skyweaver.core.states.air_space_state import AirspaceState
from skyweaver.scenarios.components.voronoi.scipy_voronoi import ScipyVoronoi


class VoronoiConfiguration:
    """
    Configuration view for the Voronoi layer.

    Takes centroids (usually from the clustering step),
    generates bounded Voronoi cells, and updates the AirspaceState.
    """

    def __init__(
        self,
        centroids: List[Point],
        domain: tuple,
        generator: ScipyVoronoi | None = None,
    ):
        self.centroids = centroids
        self.domain = domain
        self.generator = generator or ScipyVoronoi()

        # Run and sync
        self.cells: Dict[str, List[Point]] = self._generate_cells()
        self._sync_to_airspace_state()

    def _generate_cells(self) -> Dict[str, List[Point]]:
        """Compute bounded Voronoi cells using the chosen generator."""
        self.generator.fit(self.centroids, self.domain)
        cells = {
            label: cell.vertices for label, cell in self.generator.get_cells().items()
        }
        return cells

    def _sync_to_airspace_state(self) -> None:
        """Synchronize Voronoi cells to the global AirspaceState singleton."""
        state = AirspaceState()
        state.reset_voronoi()
        state.voronoi_cells = self.cells
        state.increment_step()
        state._mark_update("voronoi")

    def summary(self) -> str:
        """Return human-readable summary."""
        return (
            f"VoronoiConfiguration\n"
            f"--------------------\n"
            f"Domain: {self.domain}\n"
            f"Centroids: {len(self.centroids)}\n"
            f"Voronoi Cells: {len(self.cells)}"
        )


# =====================================================
# Manual test
# =====================================================
if __name__ == "__main__":
    from skyweaver.scenarios.components.cluster.hdbscan_cluster import HDBSCANCluster
    from skyweaver.scenarios.components.distributions.uav_mav_uav_distribution import (
        UAVMAVUAVDistribution,
    )
    import numpy as np

    rng = np.random.default_rng(42)
    dist = UAVMAVUAVDistribution(rng=rng)
    config = dist.config

    clusterer = HDBSCANCluster(random_state=42)
    clusterer.fit(config, k=list(range(2, 8)))
    centroids = clusterer.get_centroids()

    vor_config = VoronoiConfiguration(centroids=centroids, domain=config.domain)
    print(vor_config.summary())

    state = AirspaceState()
    print("\n", state.summary())
