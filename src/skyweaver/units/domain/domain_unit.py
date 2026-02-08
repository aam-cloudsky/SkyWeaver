from typing import Optional, Tuple

from shapely.geometry import Point

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.domain.logistics.domain_outpost import DomainOutpost
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
import math


class DomainUnit(OperationalUnit[DomainOutpost]):
    """
    A DomainUnit is a specialized OperationalUnit that focuses on domain-specific operations and logic.
    It serves as a foundational building block for units that require domain-specific functionality,
    such as handling domain-specific data, implementing domain-specific algorithms, or managing
    domain-specific interactions within the system.
    """

    BOUNDARY_OFFSET_IN_METERS = 1000.0

    def __init__(self, outpost: Optional[DomainOutpost] = None):
        if outpost is None:
            outpost = DomainOutpost()

        super().__init__(outpost)

    def run(
        self,
        centroid: Optional[Point] = None,
        domain: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None,
    ) -> None:

        domain_parcel = self._compute_domain_parcel(centroid, domain)

        with self._outpost:
            self._outpost.domain = domain_parcel

    def _compute_domain_parcel(
        self,
        centroid: Optional[Point] = None,
        domain: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None,
    ):

        if domain is None:
            heliports = self._outpost.heliports_parcel.heliports
            vertiports = self._outpost.vertiports_parcel.vertiports
            centroid = self._centroid(heliports, vertiports)
            max_distance = self._max_distance_from_centroid(
                centroid, heliports, vertiports
            )
            distance = math.ceil(max_distance + self.BOUNDARY_OFFSET_IN_METERS)
            domain = (
                (centroid.x - distance, centroid.x + distance),
                (centroid.y - distance, centroid.y + distance),
            )
            domain_parcel: DomainParcel = DomainParcel(domain=domain, centroid=centroid)

        elif domain is not None and centroid is not None:
            domain_parcel: DomainParcel = DomainParcel(domain, centroid)
        elif domain is not None and centroid is None:
            domain_parcel: DomainParcel = DomainParcel(domain=domain)
        return domain_parcel

    def _centroid(self, heliports: list[Point], vertiports: list[Point]) -> Point:

        all_points = heliports + vertiports
        if not all_points:
            return Point(0.0, 0.0)
        x_coords = [point.x for point in all_points]
        y_coords = [point.y for point in all_points]
        centroid_x = sum(x_coords) / len(all_points)
        centroid_y = sum(y_coords) / len(all_points)
        return Point(centroid_x, centroid_y)

    def _max_distance_from_centroid(
        self, centroid: Point, heliports: list[Point], vertiports: list[Point]
    ) -> float:

        all_points = heliports + vertiports
        if not all_points:
            return 0.0
        max_distance = max(centroid.distance(point) for point in all_points)
        return max_distance
