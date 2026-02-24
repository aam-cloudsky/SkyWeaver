from dataclasses import dataclass
from skyweaver.units.yaml_loader.base_parameters import BaseParameters


@dataclass
class DomainParameters(BaseParameters):
    yaml_section = "domain"

    padding: float
    margin: float
