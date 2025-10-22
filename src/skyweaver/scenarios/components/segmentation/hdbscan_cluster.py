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
from scipy.interpolate import PchipInterpolator

class HDBSCANCluster(BaseCluster):
    """
    Adaptive clusterer combining HDBSCAN density estimation for:
      - UAV Points of Interest (dynamic layer)
      - MAV Points of Interest (structural layer)
    """

    def __init__(self):
        super().__init__()


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
        print(f"[INFO] Running HDBSCAN on {len(points)} points → min_cluster_size={min_cluster_size}, min_samples={min_samples}")

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
            print("[WARNING] All points marked as noise — overriding: all points assigned to one cluster (label 0).")
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

        print(f"Fitting HDBSCANCluster with {len(uav_points)} UAV points and {len(mav_points)} MAV points")
        uav_clusters, uav_score, uav_info = self._fit(uav_points, min_samples)
        mav_clusters, mav_score, mav_info = self._fit(mav_points, min_samples)

        self.uav_clusters_ = uav_clusters
        self.mav_clusters_ = mav_clusters

        with config:
            for label, pts in uav_clusters.items():
                    config.clusters[f"UAV_{label}"] = pts
                    config.types[f"UAV_{label}"] = "UAV"

            for label, pts in mav_clusters.items():
                    config.clusters[f"MAV_{label}"] = pts
                    config.types[f"MAV_{label}"] = "MAV"

        best_score_ = (uav_score + mav_score) / 2.0
        return {"uav": uav_info, "mav": mav_info, "avg_score": float(best_score_)}


    def generate(self):
        """Compute and store centroids, boundaries, and polygons in ClusterConfiguration."""

        self.fit()
        config = ClusterConfiguration()

        print(f"[INFO] Generating cluster configuration for {len(config.clusters)} clusters.")

        for label, points in config.clusters.items():
            if not points:
                print(f"[WARNING] Cluster {label} has no points; skipping centroid calculation.")
                continue

            print(f"[INFO] Calculating centroid for cluster {label} with {len(points)} points.")

            arr = np.array([[p.x, p.y] for p in points])
            cx, cy = arr.mean(axis=0)
            centroid = Point(x=cx, y=cy)

            with config:
                config.centroids[label] = centroid
                config.types[label] = "UAV" if "UAV" in label else "MAV" if "MAV" in label else "Unknown"


        boundaries, polygons_info = self.cluster_boundary.get_cluster_boundaries(boundary_margin=80.0)

        for label, geom in boundaries.items():
            if isinstance(geom, Polygon):
                boundary_points = [Point(x, y) for x, y in zip(*geom.exterior.xy)]

                with config:
                    config.boundaries[label] = boundary_points
                    config.polygons[label] = geom

            else:
                print(f"[WARNING] Cluster {label} has non-polygon geometry; skipping boundary and polygon assignment.")



        print(f"[INFO] Generated {len(config.centroids)} centroids, {len(config.boundaries)} boundaries, and {len(config.polygons)} polygons.")
        return config

    # ==========================================================
    # Centroid calculation
    # ==========================================================
    def get_centroids(self) -> List[Point]:
        """Return latest centroids from AirspaceState."""
        return list(ClusterConfiguration().centroids.values())

   




    

    # ==========================================================
    # Visualization
    # ==========================================================
    def plot(self, title="HDBSCAN Clusters (UAV + MAV)"):
        config = ClusterConfiguration()
        if not config.clusters:
            print("⚠️ No clusters to plot. Run `fit()` first.")
            return

        import matplotlib.cm as cm
        cmap = cm.get_cmap("tab10", len(config.clusters))
        colors = cmap(np.arange(len(config.clusters)))

        plt.figure(figsize=(8, 8))
        plt.title(title)
        plt.xlabel("X")
        plt.ylabel("Y")

        for i, (label, points) in enumerate(config.clusters.items()):
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

        boundaries, info = self.cluster_boundary.get_cluster_boundaries(boundary_margin=80)

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

    clusterer = HDBSCANCluster()
    config = clusterer.generate()
    clusterer.plot(title="HDBSCAN Clusters (UAV + MAV)")

    print(config.clusters)
    #clusterer.plot(title="UAV and MAV Clusters with Centroids")
