# src/skyweaver/discretization/grid/grid_parcel.py
# horrible name.

from dataclasses import dataclass, field

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.grid.structure.nullgrid import NullGrid
from skyweaver.grid.structure.basegrid import BaseGrid



@dataclass
class GridParcel(Parcel):
    grid: BaseGrid = field(default_factory=NullGrid)
    cell_size: float = field(default=100.0)

