from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.sources.logistics.heliports_parcel import HeliportsParcel
from skyweaver.units.sources.logistics.vertiports_parcel import VertiportsParcel


@dataclass
class DomainOutpost(Outpost):
    domain: DomainParcel = field(
        default_factory=DomainParcel, metadata={"role": ParcelRole.PRODUCED}
    )

    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )
