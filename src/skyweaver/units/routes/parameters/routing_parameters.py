from dataclasses import dataclass
from typing import ClassVar

from skyweaver.units.yaml_loader.base_parameters import BaseParameters


@dataclass
class RoutingParameters(BaseParameters):
    yaml_section: ClassVar[str] = "routing"

    connectivity_mode: str = "all_pairs"
    k_neighbors: int = 2
