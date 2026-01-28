# core/logistics/parcel.py

from dataclasses import dataclass
from abc import ABC
from enum import Enum, auto

class ParcelRole(Enum):
    """Role of a parcel in an Outpost."""
    CONSUMED = auto()   # dependency
    PRODUCED = auto()   # owned / produced here
    UNDEFINED = auto()  # undefined role

class Parcel(ABC):
    """
    Semantic unit transported via Depot.
    """
    pass


@dataclass
class EmptyParcel(Parcel):
    pass
