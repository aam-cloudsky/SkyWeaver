from dataclasses import dataclass, field

from skyweaver.core.logistics.endpoint.outpost import Outpost
from skyweaver.core.logistics.parcel.parcel import ParcelRole
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.sources.logistics.geodata_parcel import GeoDataParcel
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


@dataclass
class DomainOutpost(Outpost):

    geodata: GeoDataParcel = field(
        default_factory=GeoDataParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    domain_parcel: DomainParcel = field(
        default_factory=DomainParcel, metadata={"role": ParcelRole.PRODUCED}
    )

    yaml_parcel: YAMLParcel = field(
        default_factory=YAMLParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )
