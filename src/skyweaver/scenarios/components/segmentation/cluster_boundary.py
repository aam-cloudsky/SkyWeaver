from abc import ABC, abstractmethod
from typing import List
from skyweaver.core.geometry.point import Point
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from skyweaver.scenarios.components.cluster.cluster_configuration import ClusterConfiguration


from shapely.geometry import LineString, Polygon, Point as ShapelyPoint
from shapely.ops import unary_union
from scipy.interpolate import UnivariateSpline
import numpy as np


from skyweaver.scenarios.components.cluster.cluster_configuration import ClusterConfiguration



class ClusterBoundary():
    def __init__(self):
       pass

   # ==========================================================
   # Boundary generation
   # ==========================================================

    def get_cluster_boundaries(self, min_radius=50.0, boundary_margin=100.0):
        """
        Hybrid boundary generator:
        - 1 point → disk
        - 2 points → line buffer
        - 3+ points → smooth radial spline
        """
        boundaries = {}
        info = {}

        config = ClusterConfiguration()
        for label, points in config.clusters.items():
            if not points:
                continue

            arr = np.array([[p.x, p.y] for p in points])
            cx, cy = arr.mean(axis=0)
            n = len(points)

            if n == 1:
                geom = ShapelyPoint(cx, cy).buffer(min_radius)
            elif n == 2:
                geom = LineString(arr).buffer(boundary_margin)
            else:
                try:
                    geom = self.smooth_radial_boundary(
                        arr, offset=boundary_margin, smoothness=3.0)
                except Exception as e:
                    print(f"[WARNING] Fallback for cluster {label}: {e}")
                    disks = [ShapelyPoint(p.x, p.y).buffer(
                        boundary_margin) for p in points]
                    geom = unary_union(disks)

            radius = max(np.linalg.norm(
                arr - np.array([cx, cy]), axis=1)) + boundary_margin

            boundaries[label] = geom
            info[label] = {
                "centroid": (cx, cy),
                "radius": radius,
                "n_points": n,
                "is_disk": n == 1,
            }

        return boundaries, info

    # ==========================================================
    # Stable smooth boundary generator
    # ==========================================================
    def smooth_radial_boundary(
        self,
        points: np.ndarray,
        centroid: tuple[float, float] | None = None,
        offset: float = 100.0,
        smoothness: float = 1.5,
        resolution: int = 360,
        min_angle_gap_deg: float = 20.0,
    ):
        """
        Builds a continuous, smooth boundary where:
            r(θ_real) = r_existent + offset  (real cluster directions)
            r(θ_gap)  = offset                (intermediate directions)
        Ensures continuity by adding 1°-spaced virtual points
        that are at least `min_angle_gap_deg` away from any real point.
        """
        # --- 1. Determine centroid ---
        if centroid is None:
            cx, cy = points.mean(axis=0)
        else:
            cx, cy = centroid

        # --- 2. Convert to polar coordinates ---
        dx, dy = points[:, 0] - cx, points[:, 1] - cy
        real_angles = np.arctan2(dy, dx)
        real_radii = np.sqrt(dx**2 + dy**2) + offset  # r_existent + offset

        # Normalize angles to [-π, π]
        real_angles = np.mod(real_angles + np.pi, 2 * np.pi) - np.pi

        # --- 3. Generate virtual angles ---
        full_angles = np.linspace(-np.pi, np.pi, resolution)
        full_radii = np.full_like(full_angles, offset)

        # --- 4. Remove virtual points too close to real points ---
        min_gap = np.deg2rad(min_angle_gap_deg)
        valid_mask = np.ones_like(full_angles, dtype=bool)
        for a in real_angles:
            too_close = np.abs(full_angles - a) < min_gap
            valid_mask &= ~too_close

        virtual_angles = full_angles[valid_mask]
        virtual_radii = full_radii[valid_mask]

        # --- 5. Merge real + virtual ---
        all_angles = np.concatenate([real_angles, virtual_angles])
        all_radii = np.concatenate([real_radii, virtual_radii])

        # --- 6. Sort and close the curve ---
        order = np.argsort(all_angles)
        all_angles, all_radii = all_angles[order], all_radii[order]
        all_angles = np.concatenate([all_angles, [all_angles[0] + 2 * np.pi]])
        all_radii = np.concatenate([all_radii, [all_radii[0]]])

        print(
            f"[DEBUG] Boundary points: {all_angles} (real: {len(real_angles)}, virtual: {len(virtual_angles)})")

        # --- 7. Fit smooth spline ---
        # spline = PchipInterpolator(all_angles, all_radii)
        spline = UnivariateSpline(all_angles, all_radii, s=smoothness)
        theta = np.linspace(all_angles.min(), all_angles.max(), resolution * 2)
        r_smooth = np.asarray(spline(theta), dtype=float)

        # Limit to max real radius + offset
        r_max = np.max(all_radii)
        r_smooth = np.clip(r_smooth, 0, r_max + offset)

        # Optional small median filter to remove small spikes
        from scipy.signal import medfilt
        r_smooth = medfilt(r_smooth, kernel_size=5)

        # --- 8. Safety clamp ---
        r_smooth = np.clip(r_smooth, offset, None)

        # --- 9. Convert back to Cartesian ---
        x = cx + r_smooth * np.cos(theta)
        y = cy + r_smooth * np.sin(theta)

        return Polygon(np.column_stack([x, y]))
