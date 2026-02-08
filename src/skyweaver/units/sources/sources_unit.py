from typing import Optional

from shapely import Point
from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.sources.logistics.sources_outpost import SourcesOutpost
import random
from typing import List, Tuple


class SourcesUnit(OperationalUnit[SourcesOutpost]):
    def __init__(self, outpost: Optional[SourcesOutpost] = None):
        if outpost is None:
            outpost = SourcesOutpost()
        super().__init__(outpost)

    def run(self) -> None:
        heliports, vertiports = self._simulate_sources()
        with self._outpost:
            self._outpost.heliports_parcel.heliports = heliports
            self._outpost.vertiports_parcel.vertiports = vertiports

    def add_heliport(self, location: Point) -> None:
        with self._outpost:
            self._outpost.heliports_parcel.heliports.append(location)

    def add_vertiport(self, location: Point) -> None:
        with self._outpost:
            self._outpost.vertiports_parcel.vertiports.append(location)

    # ====================================================================
    # Simulated data generation methods
    # ====================================================================

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
