from typing import Optional

from shapely import Point
from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.sources.logistics.geodata_parcel import GeoDataParcel
from skyweaver.units.sources.logistics.sources_outpost import SourcesOutpost
import random
from typing import List, Tuple
import pathlib
import geopandas as gpd

from skyweaver.units.sources.sources_parameters import SourcesParameters


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

    # ==========================================================================================
    # Loading Data
    # ==========================================================================================

    def _path_validity(self, path: str) -> Tuple[str, bool]:

        if not path:
            return path, False

        p = pathlib.Path(path)

        if not p.is_absolute():
            p = (pathlib.Path.cwd() / p).resolve()

        if not p.exists():
            print(f"[Warning] Path does not exist: {p}")
            return str(p), False

        if not p.is_file():
            print(f"[Warning] Not a file: {p}")
            return str(p), False

        return str(p), True

    def _load_data(self, path: str) -> gpd.GeoDataFrame:
        path, valid = self._path_validity(path)
        if not valid:
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

        return gpd.read_file(path)

    def _load_geodata(self) -> GeoDataParcel:
        parameters: SourcesParameters = SourcesParameters.from_yaml_parcel(
            self._outpost.yaml_parcel
        )

        heliports = self._load_data(parameters.heliports_path)

        print(f"Loaded {len(heliports)} heliports from {parameters.heliports_path}")
        vertiports = self._load_data(parameters.vertiports_path)

        return GeoDataParcel(
            heliports=heliports,
            vertiports=vertiports,
        )

    # ==========================================================================================
    # Simulating Data
    # ==========================================================================================

    def _simulate_geodata(self) -> GeoDataParcel:
        heliports, vertiports = self._simulate_sources()

        heliports_gdf = gpd.GeoDataFrame(geometry=heliports, crs="EPSG:4326")

        vertiports_gdf = gpd.GeoDataFrame(geometry=vertiports, crs="EPSG:4326")

        return GeoDataParcel(
            heliports=heliports_gdf,
            vertiports=vertiports_gdf,
        )

    def _simulate_sources(
        self, n_heliports: int = 5, n_vertiports: int = 5
    ) -> Tuple[List[Point], List[Point]]:
        domain = self._get_random_space()
        heliports = self._get_random_locations(domain, number=n_heliports)
        vertiports = self._get_random_locations(domain, number=n_vertiports)
        return (heliports, vertiports)

    def _get_random_space(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        return (random.uniform(0, 10000), random.uniform(0, 10000)), (
            random.uniform(0, 10000),
            random.uniform(0, 10000),
        )

    def _get_random_locations(
        self,
        domain: Tuple[Tuple[float, float], Tuple[float, float]],
        number: int,
    ) -> List[Point]:
        "gen random locations within domain"
        (xmin, xmax), (ymin, ymax) = domain
        return [
            Point(random.uniform(xmin, xmax), random.uniform(ymin, ymax))
            for _ in range(number)
        ]
