from abc import ABC, abstractmethod
from typing import List
from skyweaver.core.geometry.point import Point
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm


class BaseCluster(ABC):
    """
    Abstract base class for all clustering algorithms in SkyWeaver.

    Provides a unified plotting interface and defines the core contract
    for implementing clustering logic and centroid computation.
    """

    # ==========================================================
    # Abstract Methods (to be implemented by subclasses)
    # ==========================================================
    @abstractmethod
    def get_centroids(self) -> List[Point]:
        """Return the centroids of the last fitted clusters."""
        pass

    # ==========================================================
    # Visualization Utility
    # ==========================================================
    def plot(
        self,
        ax=None,
        title: str = "Identified Clusters",
        cmap: str = "viridis"
    ):
        """
        Display a 2D scatter plot of the identified clusters and their centroids.

        Args:
            ax: Optional matplotlib Axes instance (for composing multiple subplots).
            title: Plot title.
            cmap: Colormap name (e.g., 'viridis', 'plasma', 'Set2', 'cividis').
        """
        if not getattr(self, "clusters_", None):
            print("[Warning] No clusters found. Run fit() or iterate() first.")
            return

        # Create axis if not provided
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))

        n_clusters = len(self.clusters_)  # type: ignore
        colormap = cm.get_cmap(cmap, n_clusters)
        colors = colormap(np.linspace(0, 1, n_clusters))

        # Plot each cluster
        for i, (label, points) in enumerate(self.clusters_.items()):  # type: ignore
            arr = np.array([[p.x, p.y] for p in points])
            if str(label).startswith("UAV_"):
                marker, edgecolor = "o", "black"
            elif str(label).startswith("MAV_"):
                marker, edgecolor = "^", "gray"
            else:
                marker, edgecolor = "s", "none"

            ax.scatter(
                arr[:, 0],
                arr[:, 1],
                s=40,
                color=colors[i],
                marker=marker,
                edgecolors=edgecolor,
                label=f"{label}"
            )

        # Plot centroids
        centroids = self.get_centroids()
        centroids_arr = np.array([[c.x, c.y] for c in centroids])
        ax.scatter(
            centroids_arr[:, 0],
            centroids_arr[:, 1],
            c="black",
            marker="x",
            s=120,
            label="Centroids"
        )

        # Formatting
        ax.set_title(title)
        ax.set_xlabel("X coordinate")
        ax.set_ylabel("Y coordinate")
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        plt.show()
