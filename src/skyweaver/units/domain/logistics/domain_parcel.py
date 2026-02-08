# src/skyweaver/airspace/components/airspace_points.py
# maybe, i should create a outpost for domain only?
# maybe, should be _outpost.py?

from dataclasses import dataclass, field
from typing import List, Tuple
from shapely.geometry import Point
from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.domain.enums.epsg import EPSG


@dataclass
class DomainParcel(Parcel):
    domain: Tuple[Tuple[float, float], Tuple[float, float]] = field(
        default=((-1000, 1000), (-1000, 1000))
    )
    centroid: Point = field(default_factory=lambda: Point(0, 0))

    crs: EPSG = EPSG.PROJECTION_IN_METERS
