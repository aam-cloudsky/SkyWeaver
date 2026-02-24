from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


@dataclass
class YAMLOutpost(Outpost):
    yaml_parcel: YAMLParcel = field(
        default_factory=YAMLParcel, metadata={"role": ParcelRole.PRODUCED}
    )
