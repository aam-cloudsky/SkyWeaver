from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel

from skyweaver.units.geodata_domain_alignment.logistics.heliports_parcel import (
    HeliportsParcel,
)
from skyweaver.units.geodata_domain_alignment.logistics.vertiports_parcel import (
    VertiportsParcel,
)
from skyweaver.units.sources.logistics.geodata_parcel import GeoDataParcel


@dataclass
class GDProjectionOutpost(Outpost):

    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.PRODUCED}
    )

    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.PRODUCED}
    )

    geodata: GeoDataParcel = field(
        default_factory=GeoDataParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    domain: DomainParcel = field(
        default_factory=DomainParcel, metadata={"role": ParcelRole.CONSUMED}
    )
