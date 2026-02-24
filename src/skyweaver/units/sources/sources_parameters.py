from dataclasses import dataclass
from typing import ClassVar

from skyweaver.units.yaml_loader.base_parameters import BaseParameters


@dataclass
class SourcesParameters(BaseParameters):
    """Parameters for sources units."""

    yaml_section: ClassVar[str] = "sources"

    heliports_path: str
    vertiports_path: str
