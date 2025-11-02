
from enum import IntEnum, auto

class ReservedIDs(IntEnum):
    """Special routing identifiers for message delivery."""
    BROADCAST = auto()
    AIRSPACE_STATE = auto()
