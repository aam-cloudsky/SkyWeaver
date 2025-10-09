from typing import Dict, List, Any, Optional
import numpy as np
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score

from skyweaver.core.geometry.point import Point
from skyweaver.scenarios.components.distributions.configuration import DistributionConfiguration
from skyweaver.scenarios.components.cluster.base_cluster import BaseCluster


class KNNCluster(BaseCluster):
    """
    Adaptive clusterer combining KNN-based density estimation with K-Means.
    Performs two independent clustering processes:
      - one for UAV Points of Interest (dynamic layer)
      - one for MAV Points of Interest (structural layer)
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.best_k: dict[str, int] = {"uav": -1, "mav": -1}
        self.best_score_: np.float32 = np.float32(-np.inf)

        # unified container for plotting (keys are prefixed labels)
        self.clusters_: Dict[str, List[Point]] = {}

        self.uav_clusters_: Dict[int, List[Point]] = {}
        self.mav_clusters_: Dict[int, List[Point]] = {}
        self.history_: list[dict] = []

    # ==========================================================
    # Internal reusable methods
    # ==========================================================
    def _fit(self, points: list[Point], k_neighbors: int):
        """Run KNN + KMeans for a single set of points."""
        X = np.array([[p.x, p.y] for p in points], dtype=np.float32)
        if len(points) <= k_neighbors:
            raise ValueError("Number of samples smaller than k_neighbors.")

        # --- KNN-based local density ---
        nn = NearestNeighbors(n_neighbors=k_neighbors)
        nn.fit(X)
        distances, _ = nn.kneighbors(X)
        density = 1 / (np.mean(distances, axis=1) + 1e-6)
        n_clusters = max(
            2,
            int(np.clip(np.log(len(points)) * np.mean(density), 2, len(points) // 2))
        )

        # --- KMeans clustering ---
        km = KMeans(n_clusters=n_clusters, n_init=10,
                    random_state=self.random_state)
        labels = km.fit_predict(X)

        clusters: Dict[int, List[Point]] = {}
        for idx, label in enumerate(labels):
            clusters.setdefault(label, []).append(points[idx])

        score: np.float32 = np.float32(
            silhouette_score(X, labels) if n_clusters > 1 else -1
        )

        return clusters, k_neighbors, score, {
            "k": k_neighbors,
            "n_clusters": n_clusters,
            "score": score,
        }

    def _iterate(self, points: list[Point], k_values: List[int]) -> Dict[str, Any]:
        """Iterate over multiple k values and return the best configuration."""
        best_k, best_score, best_clusters = -1, np.float32(-np.inf), {}
        history = []

        for k in k_values:
            clusters, _, score, record = self._fit(points, k)
            history.append(record)
            if score > best_score:
                best_k, best_score, best_clusters = k, score, clusters

        return {
            "best_k": best_k,
            "best_score": best_score,
            "history": history,
            "clusters": best_clusters,
        }

    # ==========================================================
    # Dual clustering process: UAV + MAV
    # ==========================================================
    def fit(self, config: DistributionConfiguration, **kwargs):
        """Run separate clustering for UAV and MAV points."""
        k_values = kwargs.get("k", [2, 3, 4, 5, 6])

        uav_points = list(config.poi_uav)
        mav_points = list(config.poi_mav)

        uav_result = self._iterate(uav_points, k_values)
        mav_result = self._iterate(mav_points, k_values)

        self.uav_clusters_ = uav_result["clusters"]
        self.mav_clusters_ = mav_result["clusters"]

        # combine into unified dictionary with prefixed labels
        self.clusters_.clear()
        for idx, (label, points) in enumerate(self.uav_clusters_.items()):
            self.clusters_[f"UAV_{label}"] = points
        for idx, (label, points) in enumerate(self.mav_clusters_.items()):
            self.clusters_[f"MAV_{label}"] = points

        # store best configuration info
        self.best_k = {
            "uav": uav_result["best_k"], "mav": mav_result["best_k"]}
        self.best_score_ = np.float32(
            (uav_result["best_score"] + mav_result["best_score"]) / 2.0
        )

        # return structured results
        return {"uav": uav_result, "mav": mav_result}

    # ==========================================================
    # Centroid calculation
    # ==========================================================
    def get_centroids(self) -> List[Point]:
        """Compute centroids from the unified cluster dictionary."""
        centroids = []
        for cluster_points in self.clusters_.values():
            arr = np.array([[p.x, p.y] for p in cluster_points])
            cx, cy = arr.mean(axis=0)
            centroids.append(Point(cx, cy))
        return centroids


# ==========================================================
# Stand-alone test (manual execution)
# ==========================================================

if __name__ == "__main__":
    from skyweaver.scenarios.components.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(42)
    distribution = UAVMAVUAVDistribution(rng=rng)
    config = distribution.config

    clusterer = KNNCluster(random_state=42)
    result = clusterer.fit(config, k=list(range(2, 8)))

    # Debug
    print("\n=== UAV CLUSTERS ===")
    for e in result["uav"]["history"]:
        print(f"k={e['k']}, n_clusters={e['n_clusters']}, score={e['score']:.4f}")

    print("\n=== MAV CLUSTERS ===")
    for e in result["mav"]["history"]:
        print(f"k={e['k']}, n_clusters={e['n_clusters']}, score={e['score']:.4f}")

    # Plota clusters (ambos)
    clusterer.plot(title="UAV and MAV Clusters (Independent Fits)")
