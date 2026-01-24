# src/skyweaver/planning/graph/graph_outpost.py
from skyweaver.instance_segmentation.clustering.cluster_parcel import ClusterParcel

from skyweaver.discretization.grid.grid_parcel import GridParcel
from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost


@dataclass
class GraphOutpost(Outpost):
    """
    Declarative structural view of the clustering state within the AirspaceState.

    Each cluster is represented by:
        - a unique ID (e.g., 'UAV_0', 'MAV_1')
        - a set of member points
        - a centroid
        - a boundary (list of perimeter points)
        - a polygon (solid geometric region)
        - a type label ('UAV' or 'MAV')
    """

    cluster_parcel: ClusterParcel = field(default_factory=ClusterParcel)
    grid_parcel: GridParcel = field(default_factory=GridParcel)
