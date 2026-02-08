# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py

from dataclasses import dataclass, field
from skyweaver.core.logistics.outpost import Outpost

from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.clustering.logistics.cluster_parcel import ClusterParcel
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.grid.logistics.grid_parcel import GridParcel


@dataclass
class GridOutpost(Outpost):
    """
    Hex grid builder outpost.
    """

    cluster_parcel: ClusterParcel = field(
        default_factory=ClusterParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    grid_parcel: GridParcel = field(
        default_factory=GridParcel,
        metadata={"role": ParcelRole.PRODUCED},
    )

    domain_parcel: DomainParcel = field(
        default_factory=DomainParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )
