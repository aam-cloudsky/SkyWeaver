# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py

from dataclasses import dataclass, field
from typing import Optional
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

    airspace_points: Optional[AirspacePoints] = field(
        default=None,
        metadata={"role": ParcelRole.CONSUMED},
    )

    cluster_parcel: Optional[ClusterParcel] = field(
        default=None,
        metadata={"role": ParcelRole.CONSUMED},
    )

    grid_parcel: Optional[GridParcel] = field(
        default=None,
        metadata={"role": ParcelRole.PRODUCED},
    )
