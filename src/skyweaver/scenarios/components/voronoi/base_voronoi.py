# src/skyweaver/scenarios/components/voronoi/base_voronoi.py

import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict
from skyweaver.core.geometry.point import Point

import plotly.graph_objects as go

class BaseVoronoi(ABC):
    """
    Abstract base class for Voronoi diagram generators.
    """

    @abstractmethod
    def fit(self, centroids: List[Point], domain: tuple) -> None:
        """Generate the Voronoi diagram within the given domain."""
        pass

    @abstractmethod
    def get_cells(self) -> Dict[str, List[Point]]:
        """Return a dictionary mapping each cell to its vertices."""
        pass

    import plotly.graph_objects as go

    def voronoi_finite_polygons_2d(self, radius=None):
        """
        Reconstruct infinite Voronoi regions in a 2D diagram to finite
        regions clipped within a specified radius.

        Based on: https://stackoverflow.com/a/20678647
        """
        if self.points.shape[1] != 2:
            raise ValueError("Requires 2D input")

        new_regions = []
        new_vertices = self.vertices.tolist()

        center = self.points.mean(axis=0)
        if radius is None:
            radius = self.points.ptp().max() * 2

        # Map ridge vertices to all ridges for each point
        all_ridges = {}
        for (p1, p2), (v1, v2) in zip(self.ridge_points, self.ridge_vertices):
            all_ridges.setdefault(p1, []).append((p2, v1, v2))
            all_ridges.setdefault(p2, []).append((p1, v1, v2))

        # Reconstruct infinite regions
        for p1, region_idx in enumerate(self.point_region):
            vertices = self.regions[region_idx]
            if all(v >= 0 for v in vertices):
                new_regions.append(vertices)
                continue

            ridges = all_ridges[p1]
            new_region = [v for v in vertices if v >= 0]

            for p2, v1, v2 in ridges:
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0:
                    continue

                # Compute the missing endpoint of infinite ridge
                t = self.points[p2] - self.points[p1]
                t /= np.linalg.norm(t)
                n = np.array([-t[1], t[0]])  # normal vector

                midpoint = self.points[[p1, p2]].mean(axis=0)
                direction = np.sign(np.dot(midpoint - center, n)) * n
                far_point = self.vertices[v2] + direction * radius

                new_vertices.append(far_point.tolist())
                new_region.append(len(new_vertices) - 1)

            # Sort region vertices counterclockwise
            vs = np.asarray([new_vertices[v] for v in new_region])
            c = vs.mean(axis=0)
            angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
            new_region = np.array(new_region)[np.argsort(angles)]
            new_regions.append(new_region.tolist())

        return new_regions, np.asarray(new_vertices)
