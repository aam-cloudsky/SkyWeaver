# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py

from dataclasses import dataclass, field
from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.clustering.logistics.cluster_parcel import ClusterParcel
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.grid.logistics.grid_parcel import GridParcel
from skyweaver.units.routes.logistics.routes_parcel import RoutesParcel
from skyweaver.units.sources.logistics.heliports_parcel import HeliportsParcel
from skyweaver.units.sources.logistics.vertiports_parcel import VertiportsParcel


@dataclass
class VizOutpost(Outpost):
    """
    Hex grid builder outpost.
    """

    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )
    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    domain_parcel: DomainParcel = field(
        default_factory=DomainParcel, metadata={"role": ParcelRole.CONSUMED}
    )
    grid_parcel: GridParcel = field(
        default_factory=GridParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    cluster_parcel: ClusterParcel = field(
        default_factory=ClusterParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    routes_parcel: RoutesParcel = field(
        default_factory=RoutesParcel, metadata={"role": ParcelRole.CONSUMED}
    )
