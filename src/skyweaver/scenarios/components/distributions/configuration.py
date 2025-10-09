from dataclasses import dataclass
from typing import Tuple
from skyweaver.core.geometry.point import Point
from skyweaver.core.states.air_space_state import AirspaceState


@dataclass(frozen=True)
class DistributionConfiguration:
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """
    domain: Tuple[Tuple[float, float], Tuple[float, float]]
    poi_uav: Tuple[Point, ...]
    poi_mav: Tuple[Point, ...]

    def __post_init__(self):
        self._sync_to_airspace_state()

    def _sync_to_airspace_state(self):
        """
        Updates only the distribution-related attributes of the AirspaceState.
        Other layers (clusters, voronoi, etc.) remain unchanged.

        AirspaceState is a singleton per thread, so this ensures thread-safe updates.
        """
        state = AirspaceState()
        state.reset_distribution()  # only clears distribution-related parts
        state.domain = self.domain
        state.uav_points[:] = list(self.poi_uav)
        state.mav_points[:] = list(self.poi_mav)
