import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d
from typing import List, Dict

from shapely import Point

from skyweaver.scenarios.components.voronoi.base_voronoi import BaseVoronoi
from skyweaver.scenarios.components.voronoi.voronoi_cell import VoronoiCell


class ScipyVoronoi(BaseVoronoi):
    """
    Voronoi diagram generator using SciPy.
    Handles bounded domains and maps each centroid to a polygon region.
    """

    def __init__(self):
        self.voronoi_: Voronoi | None = None
        self.cells_: Dict[str, VoronoiCell] = {}

    def fit(self, centroids: List[Point], domain: tuple):
        """Generate Voronoi diagram bounded within the domain."""
        self.centroids = centroids
        self.points = np.array(
            [[p.x, p.y] for p in centroids], dtype=np.float32
        )  # 👈 add this
        self.voronoi_ = Voronoi(self.points)

        # (Optional) Clip the diagram to the domain later
        self._generate_cells(domain)

    def _generate_cells(self, domain: tuple):
        """Convert Voronoi regions into bounded polygons."""
        if self.voronoi_ is None:
            raise RuntimeError("Voronoi diagram not computed yet.")

        # Reconstruct finite regions
        regions, vertices = self.voronoi_finite_polygons_2d()

        # Domain box (for clipping)
        (x_min, x_max), (y_min, y_max) = domain
        box = np.array([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]])

        for i, region in enumerate(regions):
            polygon = vertices[region]

            # Clip polygon to bounding box
            polygon[:, 0] = np.clip(polygon[:, 0], x_min, x_max)
            polygon[:, 1] = np.clip(polygon[:, 1], y_min, y_max)

            label = f"CELL_{i}"
            self.cells_[label] = VoronoiCell(
                label, self.centroids[i], [Point(x, y) for x, y in polygon]
            )

    def get_cells(self) -> Dict[str, VoronoiCell]:
        return self.cells_


if __name__ == "__main__":
    from skyweaver.scenarios.components.cluster.hdbscan_cluster import HDBSCANCluster
    from skyweaver.scenarios.components.distributions.uav_mav_uav_distribution import (
        UAVMAVUAVDistribution,
    )

    rng = np.random.default_rng(42)
    distribution = UAVMAVUAVDistribution(rng=rng)
    config = distribution.config

    # 1️⃣ Cluster UAVs and MAVs
    clusterer = HDBSCANCluster()

    # 2️⃣ Generate Voronoi diagram from centroids
    centroids = clusterer.get_centroids()
    vor = ScipyVoronoi()


