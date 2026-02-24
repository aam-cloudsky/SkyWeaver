# skyweaver/units/domain/logistics/domain_parcel.py

from dataclasses import dataclass, field
from skyweaver.core.logistics.parcel import Parcel


@dataclass(frozen=True)
class YAMLParcel(Parcel):
    yaml_fields: dict = field(default_factory=dict)
