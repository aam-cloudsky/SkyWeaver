from dataclasses import dataclass, field, fields
from skyweaver.airspace.airspace_state import AirspaceState

@dataclass
class BaseConfiguration:
    """Reactive configuration mixin that syncs assignments with AirspaceState."""

    _transaction_open: bool = field(default=True, init=False, repr=False)

    def __post_init__(self):
        """Hook called automatically by dataclasses."""
        self._load()
        object.__setattr__(self, "_transaction_open", False)

    def _list_variables(self):
        """Return public dataclass field names."""
        if hasattr(self, "__dataclass_fields__"):
            return [f.name for f in fields(self) if not f.name.startswith("_")]
        return [k for k in vars(self).keys() if not k.startswith("_")]
    
    def _dict_variables(self):
        """Return a dictionary of public dataclass fields and their values."""
        return {f.name: getattr(self, f.name) for f in fields(self) if not f.name.startswith("_")}

    def _update(self, **kwargs):
        """Push matching variables to AirspaceState."""
        if not kwargs:
            return

        state = AirspaceState()
        valid_kwargs = {k: v for k, v in kwargs.items() if hasattr(state, k)}

        if valid_kwargs:
            state.update_state(source=self.__class__.__name__, **valid_kwargs)


    def _load(self):
        """Load matching variables from AirspaceState."""
        state = AirspaceState()
        for var_name in self._list_variables():
            if hasattr(state, var_name):
                object.__setattr__(self, var_name, getattr(state, var_name))

    

    def __setattr__(self, name, value):
        """Intercepts all assignments and updates AirspaceState if needed."""

        if not getattr(self, "_transaction_open", False):
            raise AttributeError(
                "Direct assignment is disabled. Please, use the context manager: 'with Configuration() as config:'."
            )
        else:
            if name in self._list_variables():
                object.__setattr__(self, name, value)


    def __enter__(self):
        # Disable auto-sync (including __setattr__)
        object.__setattr__(self, "_transaction_open", True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Re-enable and push all updates at once
        
        try:
            if exc_type is None:
                self._update(**self._dict_variables())
        finally:
            object.__setattr__(self, "_transaction_open", False)
        
