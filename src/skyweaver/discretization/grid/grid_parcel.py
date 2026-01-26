# src/skyweaver/discretization/grid/grid_parcel.py
# horrible name.

from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.null_grid import NullGrid
from dataclasses import dataclass, field


from skyweaver.core.logistics.parcel import Parcel


@dataclass
class GridParcel(Parcel):
    grid: BaseGrid = field(default_factory=NullGrid)
    cell_size: float = field(default=100.0)

