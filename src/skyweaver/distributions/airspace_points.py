# src/skyweaver/airspace/components/airspace_points.py
#maybe, i should create a outpost for domain only?
#maybe, should be _outpost.py?

from dataclasses import dataclass, field
from typing import List, Tuple
from shapely.geometry import Point
from skyweaver.core.logistics.parcel import Parcel


@dataclass
class AirspacePoints(Parcel):
    domain: Tuple[Tuple[float, float], Tuple[float, float]
                  ] = field(default=((-1000, 1000), (-1000, 1000)))
    uav_points: List[Point] = field(default_factory=list)
    mav_points: List[Point] = field(default_factory=list)
