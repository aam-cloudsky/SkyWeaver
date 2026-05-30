# src/skyweaver/discretization/grid/grid_parcel.py
# horrible name.

from dataclasses import dataclass, field

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid


@dataclass
class GridParcel(Parcel):
    # GRID MUST BE NULLGRID. Cannot be BaseGrid due to abstract methods.
    # cannot be HexGrid due to circular imports.
    grid: HexGrid = field(default_factory=HexGrid)
    cell_size: float = field(default=100.0)

    def serialize(self):

        return {
            "cell_size": self.grid._cell_size,
            "orientation": self.grid.projection.orientation.name,
        }
