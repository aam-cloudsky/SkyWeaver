from dataclasses import dataclass, field
from pathlib import Path

from skyweaver.core.logistics.parcel.parcel import Parcel


@dataclass(frozen=True)
class YAMLParcel(Parcel):
    yaml_fields: dict = field(default_factory=dict)

    config_dir: Path = field(default_factory=Path.cwd)
