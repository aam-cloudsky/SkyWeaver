from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.hexgrid.grid_construction import build_grid
from skyweaver.units.hexgrid.logistics.grid_outpost import GridOutpost
from skyweaver.units.yaml_loader.parcel_conversion import configuration_of


class HexGridUnit(OperationalUnit[GridOutpost]):

    def __init__(self, outpost: Optional[GridOutpost] = None):

        super().__init__(outpost or GridOutpost())

    def run(self):

        domain = self._outpost.domain_parcel.domain

        if domain is None:
            raise ValueError("HexGridUnit requires a valid Domain instance.")

        grid = build_grid(domain, configuration_of(self._outpost.yaml_parcel))

        with self._outpost:
            self._outpost.grid_parcel.grid = grid
