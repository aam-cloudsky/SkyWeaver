from enum import Enum, auto


class Role(Enum):
    """Role of synced element in an Outpost."""

    CONSUMED = auto()  # dependency
    MUTATES = auto()  # can change, but it is not the owner
    PRODUCED = auto()  # owned / produced here

    UNDEFINED = auto()  # undefined role
