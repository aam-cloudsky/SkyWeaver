# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py

from dataclasses import dataclass, field
from skyweaver.core.logistics.outpost import Outpost

from skyweaver.grid.logistics.grid_parcel import GridParcel
from skyweaver.distributions.logistics.airspace_points import AirspacePoints
from skyweaver.clustering.logistics.cluster_parcel import ClusterParcel


@dataclass
class GridOutpost(Outpost):
    """
    Hex grid builder outpost.
    """

    airspace_points: AirspacePoints = field(
        default_factory=AirspacePoints
    )
    
    cluster_parcel: ClusterParcel = field(
        default_factory=ClusterParcel
    )

    grid_parcel: GridParcel = field(
        default_factory=GridParcel
    )
