
from enum import Enum, auto

class RestrictionSource(Enum):
    """
    Enumeration of sources for restrictions in the SkyWeaver grid system.

    Attributes:
        USER (int): Represents a user-defined restriction.
        SYSTEM (int): Represents a system-generated restriction.
    """
    HELIPORT = auto()
    TOWER = auto()
    AIRPORT = auto()
    TEMPORARY_ZONE = auto()
    UNKNOWN = auto()
