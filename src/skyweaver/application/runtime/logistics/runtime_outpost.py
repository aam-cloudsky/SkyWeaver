from dataclasses import dataclass, field

from skyweaver.core.logistics.endpoint.outpost import Outpost
from skyweaver.core.logistics.parcel.parcel import ParcelRole
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.geodata_domain_alignment.logistics.heliports_parcel import (
    HeliportsParcel,
)
from skyweaver.units.geodata_domain_alignment.logistics.vertiports_parcel import (
    VertiportsParcel,
)
from skyweaver.units.hexgrid.logistics.grid_parcel import GridParcel
from skyweaver.units.routes.logistics.routes_parcel import RoutesParcel
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


@dataclass
class RuntimeOutpost(Outpost):
    """
    a parcel be here implies:
        - Frontend exposition
        - serialization required
    """

    domain_parcel: DomainParcel = field(
        default_factory=DomainParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    grid_parcel: GridParcel = field(
        default_factory=GridParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    routes_parcel: RoutesParcel = field(
        default_factory=RoutesParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    yaml_parcel: YAMLParcel = field(
        default_factory=YAMLParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )
