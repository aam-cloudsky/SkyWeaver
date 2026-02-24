from dataclasses import dataclass

from skyweaver.units.hexgrid.geometry.hex_orientation import HexOrientation
from skyweaver.units.yaml_loader.base_parameters import BaseParameters


@dataclass(frozen=True)
class GridParameters(BaseParameters):

    cell_size: float
    orientation: HexOrientation
    yaml_section: str = "hexgrid"
