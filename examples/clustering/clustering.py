import matplotlib.pyplot as plt
import numpy as np
from skyweaver.clustering.hdbscan_clustering import HDBSCANClustering
from skyweaver.clustering.logistics.cluster_outpost import ClusterOutpost
from skyweaver.units.clustering.zone_type import ZoneType
from skyweaver.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution
from skyweaver.core.logistics.depot import Depot

Depot()

# ------------------------------------------------------
# 1. Initialize AirspaceState (singleton)
# ------------------------------------------------------

# ------------------------------------------------------
# 2. Generate synthetic UAV / MAV points
#    (this is expected to publish components internally)
# ------------------------------------------------------
rng = np.random.default_rng(42)

UAVMAVUAVDistribution(
    rng=rng,
    n_uav=20,
    n_mav=10,
    domain=((-1000, 1000), (-1000, 1000)),
    center_fraction=0.3,
)

# ------------------------------------------------------
# 3. Run clustering algorithm
# ------------------------------------------------------
clustering_algo = HDBSCANClustering()
clustering_algo.fit()

# ------------------------------------------------------
# 4. Retrieve clustering component from AirspaceState
# ------------------------------------------------------
cluster_outpost = ClusterOutpost()
clusters = cluster_outpost.cluster_parcel.clusters

# ------------------------------------------------------
# 5. Visualization
# ------------------------------------------------------
plt.figure(figsize=(8, 8))
plt.title("HDBSCAN Clusters (UAV + MAV)")
plt.xlabel("X")
plt.ylabel("Y")

for cluster in clusters:

    arr = np.array([[p.x, p.y] for p in cluster.source_points])
    color = "blue" if cluster.zone_type == ZoneType.UAV else "red"

    plt.scatter(arr[:, 0], arr[:, 1], color=color, s=50, alpha=0.7)

    # Cluster boundary
    x, y = cluster.polygon.exterior.xy
    plt.plot(x, y, color=color, linewidth=1.5)

    # Centroid
    plt.scatter(
        cluster.centroid.x,
        cluster.centroid.y,
        color="yellow",
        marker="*",
        s=150,
        edgecolor="black",
    )

plt.axis("equal")
plt.tight_layout()
plt.show()
