from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.sources.geodata import load_geodata, simulate_geodata
from skyweaver.units.sources.logistics.geodata_parcel import GeoDataParcel
from skyweaver.units.sources.logistics.sources_outpost import SourcesOutpost
from skyweaver.units.yaml_loader.parcel_conversion import configuration_of


class SourcesUnit(OperationalUnit[SourcesOutpost]):
    def __init__(
        self, outpost: Optional[SourcesOutpost] = None, simulation: bool = False
    ):
        if outpost is None:
            outpost = SourcesOutpost()
        super().__init__(outpost)
        self.simulation = simulation

    def run(self):
        if self.simulation:
            geodata = self._simulate_geodata()
        else:
            geodata = self._load_geodata()

        with self._outpost:
            self._outpost.geodata = geodata

    def _load_geodata(self) -> GeoDataParcel:
        geodata = load_geodata(configuration_of(self._outpost.yaml_parcel))
        return GeoDataParcel(heliports=geodata.heliports, vertiports=geodata.vertiports)

    def _simulate_geodata(self) -> GeoDataParcel:
        geodata = simulate_geodata()
        return GeoDataParcel(heliports=geodata.heliports, vertiports=geodata.vertiports)
