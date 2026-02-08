from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.sources.logistics.heliports_parcel import HeliportsParcel
from skyweaver.units.sources.logistics.vertiports_parcel import VertiportsParcel


@dataclass
class SourcesOutpost(Outpost):

    heliports_parcel: HeliportsParcel = field(
        default_factory=lambda: HeliportsParcel(),
        metadata={"role": ParcelRole.PRODUCED},
    )

    vertiports_parcel: VertiportsParcel = field(
        default_factory=lambda: VertiportsParcel(),
        metadata={"role": ParcelRole.PRODUCED},
    )
