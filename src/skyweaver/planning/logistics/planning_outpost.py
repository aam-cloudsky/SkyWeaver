# src/skyweaver/planning/graph/graph_outpost.py
from skyweaver.clustering.logistics.cluster_parcel import ClusterParcel

from skyweaver.grid.logistics.grid_parcel import GridParcel
from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.planning.logistics.planning_parcel import PlanningParcel


@dataclass
class PlanningOutpost(Outpost):
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

    grid_parcel: GridParcel = field(
        default_factory=GridParcel
    )
    cluster_parcel: ClusterParcel = field(
        default_factory=ClusterParcel
    )

    planning_parcel: PlanningParcel = field(
        default_factory=PlanningParcel
    )