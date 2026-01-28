
from enum import IntEnum, auto

class ReservedIDs(IntEnum):
    """Special routing identifiers for message delivery."""
    BROADCAST = auto()
    LOGGER = auto()
    DEPOT = auto()
