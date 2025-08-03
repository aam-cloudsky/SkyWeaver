
from enum import auto, Enum


class RestrictionShape(Enum):
    """
    Enumeration of shape types used in the SkyWeaver grid system.

    Attributes:
        SQUARE (int): Represents a square shape, typically used for grid cells.
        CIRCLE (int): Represents a circular shape, often used for areas of influence or proximity.
    """
    SQUARE = auto()
    DISK = auto()
    RECTANGLE = auto()
    CIRCULAR_SECTOR = auto()