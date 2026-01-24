# src/skyweaver/discretization/grid/hexgrid/airspace_hexgrid.py
# horrible name.


from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.null_grid import NullGrid
from dataclasses import dataclass, field


from skyweaver.core.logistics.parcel import Parcel

@dataclass
class AirspaceHexgrid(Parcel):
    grid: BaseGrid = field(default_factory=NullGrid)
