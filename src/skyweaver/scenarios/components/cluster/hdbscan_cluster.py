from shapely.geometry import LineString, Polygon, Point as ShapelyPoint
from shapely.ops import unary_union
from scipy.interpolate import UnivariateSpline
import numpy as np
import hdbscan
import matplotlib.pyplot as plt
from sklearn.metrics import davies_bouldin_score
from typing import Dict, List, Any

from skyweaver.core.geometry.point import Point
from skyweaver.scenarios.components.cluster.cluster_configuration import ClusterConfiguration
from skyweaver.scenarios.components.cluster.base_cluster import BaseCluster


class HDBSCANCluster(BaseCluster):
    """
    Adaptive clusterer combining HDBSCAN density estimation for:
      - UAV Points of Interest (dynamic layer)
      - MAV Points of Interest (structural layer)
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.best_k: dict[str, int] = {"uav": -1, "mav": -1}
        self.best_score_: float = -np.inf

        # unified container for plotting
        self.clusters_: Dict[str, List[Point]] = {}

        self.uav_clusters_: Dict[int, List[Point]] = {}
        self.mav_clusters_: Dict[int, List[Point]] = {}
        self.history_: list[dict] = []

    # ==========================================================
    # Internal reusable methods
    # ==========================================================
    def _fit(self, points: list[Point], min_samples: int = 5):
        """Run HDBSCAN clustering on a given set of points."""
        if len(points) < 3:
            clusters = {0: points}
            print(
                f"[INFO] Too few points ({len(points)}); assigning all to one cluster.")
            return clusters, 0.0, {"n_clusters": 1, "score": 0.0, "note": "too few samples"}

        X = np.array([[p.x, p.y] for p in points], dtype=np.float32)

        # Adaptive parameter tuning for small or sparse datasets
        min_cluster_size = 2
        min_samples = 2
        print(
            f"[INFO] Running HDBSCAN on {len(points)} points → min_cluster_size={min_cluster_size}, min_samples={min_samples}")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method="eom"
        )

        labels = clusterer.fit_predict(X)
        unique_labels = np.unique(labels)
        print(f"[DEBUG] HDBSCAN labels: {unique_labels}")

        # Handle case: all points labeled as noise
        if np.all(labels == -1):
            print(
                "[WARNING] All points marked as noise — overriding: all points assigned to one cluster (label 0).")
            clusters = {0: points}
            score = -10.0
            return clusters, score, {"n_clusters": 1, "score": score, "note": "forced single cluster"}

        # Build clusters normally
        clusters: Dict[int, List[Point]] = {}
        for lbl in unique_labels:
            if lbl == -1:
                continue
            clusters[int(lbl)] = [points[i]
                                  for i in range(len(points)) if labels[i] == lbl]

        # Add singleton clusters for unassigned points
        unassigned_indices = np.where(labels == -1)[0]
        if len(unassigned_indices) > 0:
            print(
                f"[INFO] {len(unassigned_indices)} points were unassigned; creating singleton clusters for them.")
            base_label = (max(clusters.keys()) + 1) if clusters else 0
            for offset, idx in enumerate(unassigned_indices):
                clusters[base_label + offset] = [points[idx]]

        n_clusters = len(clusters)
        print(f"[INFO] Identified {n_clusters} clusters (excluding noise)")

        # Compute compactness/separation score
        if n_clusters > 1:
            mask = labels >= 0
            try:
                score = -davies_bouldin_score(X[mask], labels[mask])
            except Exception:
                score = -np.inf
        else:
            score = -10.0

        return clusters, float(score), {"n_clusters": n_clusters, "score": float(score)}

    # ==========================================================
    # Public API
    # ==========================================================
    def fit(self, min_samples: int = 5) -> Dict[str, Any]:
        """Run HDBSCAN clustering for UAV and MAV points."""
        config = ClusterConfiguration()
        uav_points = list(config.uav_points)
        mav_points = list(config.mav_points)

        print(
            f"Fitting HDBSCANCluster with {len(uav_points)} UAV points and {len(mav_points)} MAV points")
        uav_clusters, uav_score, uav_info = self._fit(uav_points, min_samples)
        mav_clusters, mav_score, mav_info = self._fit(mav_points, min_samples)

        self.uav_clusters_ = uav_clusters
        self.mav_clusters_ = mav_clusters

        # Merge clusters for unified plotting
        self.clusters_.clear()
        for label, pts in uav_clusters.items():
            self.clusters_[f"UAV_{label}"] = pts
        for label, pts in mav_clusters.items():
            self.clusters_[f"MAV_{label}"] = pts

        self.best_score_ = (uav_score + mav_score) / 2.0
        return {"uav": uav_info, "mav": mav_info, "avg_score": float(self.best_score_)}

    # ==========================================================
    # Centroid calculation
    # ==========================================================
    def get_centroids(self) -> List[Point]:
        """Compute centroids from all clusters."""
        centroids = []
        for cluster_points in self.clusters_.values():
            arr = np.array([[p.x, p.y] for p in cluster_points])
            cx, cy = arr.mean(axis=0)
            centroids.append(Point(cx, cy))
        return centroids

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

        print(f"[DEBUG] Boundary points: {all_angles} (real: {len(real_angles)}, virtual: {len(virtual_angles)})")

        # --- 7. Fit smooth spline ---
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

        for label, points in self.clusters_.items():
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
    # Visualization
    # ==========================================================
    def plot(self, title="HDBSCAN Clusters (UAV + MAV)"):
        if not self.clusters_:
            print("⚠️ No clusters to plot. Run `fit()` first.")
            return

        import matplotlib.cm as cm
        cmap = cm.get_cmap("tab10", len(self.clusters_))
        colors = cmap(np.arange(len(self.clusters_)))

        plt.figure(figsize=(8, 8))
        plt.title(title)
        plt.xlabel("X")
        plt.ylabel("Y")

        for i, (label, points) in enumerate(self.clusters_.items()):
            arr = np.array([[p.x, p.y] for p in points])
            if "UAV" in label:
                marker, edgecolor = "o", "black"
            elif "MAV" in label:
                marker, edgecolor = "^", "gray"
            else:
                marker, edgecolor = "s", "none"

            plt.scatter(arr[:, 0], arr[:, 1], s=60,
                        color=colors[i], marker=marker,
                        edgecolors=edgecolor, label=label)

        centroids = self.get_centroids()
        if centroids:
            c_arr = np.array([[p.x, p.y] for p in centroids])
            plt.scatter(c_arr[:, 0], c_arr[:, 1],
                        c="yellow", marker="*", s=200,
                        edgecolor="black", linewidths=1.5, label="Centroids")

        boundaries, info = self.get_cluster_boundaries(boundary_margin=80)
        from shapely.geometry import MultiPolygon, GeometryCollection

        for label, geom in boundaries.items():
            if isinstance(geom, (GeometryCollection, MultiPolygon)):
                for subgeom in geom.geoms:
                    if isinstance(subgeom, Polygon):
                        x, y = subgeom.exterior.xy
                        plt.fill(x, y, alpha=0.15, label=f"{label} boundary")
            elif isinstance(geom, Polygon):
                x, y = geom.exterior.xy
                plt.fill(x, y, alpha=0.15, label=f"{label} boundary")

        # Remove legend frame and background
        plt.legend(frameon=False)

        # Remove all axes, ticks, and spines
        #plt.axis("equal")
        #plt.axis("off")
        #plt.grid(False)

        # Remove figure background (transparent)
        plt.gca().set_facecolor("none")
        plt.gcf().patch.set_alpha(0.0)

        plt.tight_layout(pad=0)
        plt.show()


# ==========================================================
# Stand-alone test
# ==========================================================
if __name__ == "__main__":
    from skyweaver.scenarios.components.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution

    rng = np.random.default_rng(42)
    distribution = UAVMAVUAVDistribution(rng=rng)
    config = distribution.config

    clusterer = HDBSCANCluster(random_state=42)
    result = clusterer.fit()
    print(result)
    clusterer.plot(title="UAV and MAV Clusters with Centroids")
