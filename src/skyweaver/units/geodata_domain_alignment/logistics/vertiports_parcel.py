# src/skyweaver/airspace/components/airspace_points.py
# maybe, i should create a outpost for domain only?
# maybe, should be _outpost.py?

from dataclasses import dataclass, field
from typing import List, Tuple
from shapely.geometry import Point
from skyweaver.core.logistics.parcel.parcel import Parcel


@dataclass
class VertiportsParcel(Parcel):
    vertiports: List[Point] = field(default_factory=list)
