from dataclasses import dataclass, field

from skyweaver.core.logistics.endpoint.outpost import Outpost
from skyweaver.core.logistics.parcel.parcel import ParcelRole
from skyweaver.units.geodata_domain_alignment.logistics.heliports_parcel import (
    HeliportsParcel,
)
from skyweaver.units.geodata_domain_alignment.logistics.vertiports_parcel import (
    VertiportsParcel,
)
from skyweaver.units.hexgrid.logistics.grid_parcel import GridParcel


@dataclass
class RestrictionOutpost(Outpost):
    grid_parcel: GridParcel = field(
        default_factory=GridParcel,
        metadata={"role": ParcelRole.MUTATES},
    )

    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )
