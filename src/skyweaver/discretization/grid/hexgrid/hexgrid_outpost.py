# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py

from dataclasses import dataclass, field
from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.outpost import ParcelRole

from skyweaver.discretization.grid.grid_parcel import GridParcel
from skyweaver.distributions.airspace_points import AirspacePoints
from skyweaver.clustering.cluster_parcel import ClusterParcel
from skyweaver.core.logistics.parcel import EmptyParcel, Parcel


@dataclass
class HexGridOutpost(Outpost):
    """
    Hex grid builder outpost.

    All parcels are REQUIRED dependencies.
    """

    airspace_points: AirspacePoints = field(
        default_factory=AirspacePoints,
        metadata={"role": ParcelRole.CONSUMED},
    )

    cluster_parcel: ClusterParcel = field(
        default_factory=ClusterParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    grid_parcel: GridParcel = field(
        default_factory=GridParcel,
        metadata={"role": ParcelRole.PRODUCED},
    )
