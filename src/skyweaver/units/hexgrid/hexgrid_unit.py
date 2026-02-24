from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.hexgrid.logistics.grid_outpost import GridOutpost
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.hexgrid.parameters.grid_parameters import GridParameters


class HexGridUnit(OperationalUnit[GridOutpost]):

    def __init__(self, outpost: Optional[GridOutpost] = None):

        super().__init__(outpost or GridOutpost())

        self._parameters: GridParameters = GridParameters.from_yaml_parcel(
            self._outpost.yaml_parcel
        )

    def run(self):

        domain_parcel = self._outpost.domain_parcel
        domain = domain_parcel.domain  # ✅ extract Domain object

        if domain is None:
            raise ValueError("HexGridUnit requires a valid Domain instance.")

        bounds = domain.operational_bounds  # ✅ correct level

        parameters = GridParameters.from_yaml_parcel(self._outpost.yaml_parcel)

        grid = HexGrid(
            cell_size=parameters.cell_size,
            operational_bounds=bounds,
            orientation=parameters.orientation,
        )

        with self._outpost:
            self._outpost.grid_parcel.grid = grid
