# src/skyweaver/discretization/grid/grid_parcel.py
# horrible name.

from dataclasses import dataclass, field

from skyweaver.core.logistics.parcel import Parcel

from skyweaver.units.grid.structure.basegrid import BaseGrid
from skyweaver.units.grid.structure.nullgrid import NullGrid


@dataclass
class GridParcel(Parcel):
    # GRID MUST BE NULLGRID. Cannot be BaseGrid due to abstract methods.
    # cannot be HexGrid due to circular imports.
    grid: BaseGrid = field(default_factory=NullGrid)
    cell_size: float = field(default=100.0)
