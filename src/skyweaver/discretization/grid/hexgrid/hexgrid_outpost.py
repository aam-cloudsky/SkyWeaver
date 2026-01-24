# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py
# horrible name.


from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.grid_parcel import GridParcel
from skyweaver.discretization.grid.null_grid import NullGrid
from skyweaver.distributions.airspace_points import AirspacePoints
from skyweaver.instance_segmentation.clustering.cluster_parcel import ClusterParcel
from skyweaver.instance_segmentation.geometry.cluster import Cluster

from dataclasses import dataclass, field
from typing import List, Tuple



from skyweaver.core.logistics.outpost import Outpost


@dataclass
class HexGridOutpost(Outpost):
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """

    airspace_points: AirspacePoints = field(default_factory=AirspacePoints)
    cluster_parcel: ClusterParcel = field(default_factory=ClusterParcel)
    grid_parcel: GridParcel = field(default_factory=GridParcel)




