from skyweaver.core.states.air_space_state import AirspaceState


class BaseConfiguration:
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """

    def _list_variables(self):
        """Return only public instance attributes."""
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}


    def _update(self, **kwargs):
        """
        Updates only the distribution-related attributes of the AirspaceState.
        Other layers (clusters, voronoi, etc.) remain unchanged.

        AirspaceState is a singleton per thread, so this ensures thread-safe updates.
        """
        if not kwargs:
            return

        state = AirspaceState()
        state.update_state(source=self.__class__.__name__, **kwargs)

    def _load(self):
        state = AirspaceState()
        for var_name in self._list_variables().keys():
            if hasattr(state, var_name):
                setattr(self, var_name, getattr(state, var_name))

    def __post_init__(self):
        self._load()

    def update(self, **kwargs):
        """
        Update local variables and propagate filtered subset to AirspaceState.
        """
        changed = {}
        for var_name, value in kwargs.items():
            if hasattr(self, var_name):
                object.__setattr__(self, var_name, value)
                changed[var_name] = value

        # Push only declared & compatible variables
        if changed:
            self._update(**changed)
