from dataclasses import dataclass
from typing import Tuple
from skyweaver.core.geometry.point import Point
from skyweaver.core.states.air_space_state import AirspaceState


class BaseConfiguration:
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """

    def __init__(self, configuration_name, **kwargs):
        self.configuration_name = configuration_name
        self.params = kwargs

    def __post_init__(self):
        self._sync_to_airspace_state()

    def _sync_to_airspace_state(self):
        """
        Updates only the distribution-related attributes of the AirspaceState.
        Other layers (clusters, voronoi, etc.) remain unchanged.

        AirspaceState is a singleton per thread, so this ensures thread-safe updates.
        """
        state = AirspaceState()
        state.reset(self.configuration_name, self.params)  # only clears distribution-related parts