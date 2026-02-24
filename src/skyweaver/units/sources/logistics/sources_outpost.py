from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole


from skyweaver.units.sources.logistics.geodata_parcel import GeoDataParcel
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


@dataclass
class SourcesOutpost(Outpost):

    geodata: GeoDataParcel = field(
        default_factory=GeoDataParcel,
        metadata={"role": ParcelRole.PRODUCED},
    )

    yaml_parcel: YAMLParcel = field(
        default_factory=YAMLParcel, metadata={"role": ParcelRole.PRODUCED}
    )
    # from skyweaver.units.sources.logistics.vertiports_parcel import VertiportsParcel
    # from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
    # from skyweaver.units.sources.logistics.heliports_parcel import HeliportsParcel


# heliports_parcel: HeliportsParcel = field(
#    default_factory=lambda: HeliportsParcel(),
#    metadata={"role": ParcelRole.PRODUCED},
# )

# vertiports_parcel: VertiportsParcel = field(
#    default_factory=lambda: VertiportsParcel(),
#    metadata={"role": ParcelRole.PRODUCED},
# )
