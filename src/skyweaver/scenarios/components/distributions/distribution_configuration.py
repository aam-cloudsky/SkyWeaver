from dataclasses import dataclass, field
from typing import List, Tuple

from shapely import Point

from skyweaver.core.states.base_configuration import BaseConfiguration


@dataclass
class DistributionConfiguration(BaseConfiguration):
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """
    domain: Tuple[Tuple[float, float], Tuple[float, float]] = field(default=(( -1000, 1000), (-1000, 1000)))
    uav_points: List[Point] = field(default_factory=list)
    mav_points: List[Point] = field(default_factory=list)
