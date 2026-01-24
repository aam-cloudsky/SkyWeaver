from dataclasses import dataclass


@dataclass
class Parcel:
    """Marker base class for AirspaceState components."""
    pass


@dataclass
class EmptyParcel(Parcel):
    """Empty component for default initialization."""
    pass