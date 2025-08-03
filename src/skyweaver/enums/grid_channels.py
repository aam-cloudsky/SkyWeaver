from enum import auto, Enum

class GridChannels(Enum):
    """
    Enumeration of grid channel types used in the SkyWeaver grid system.
    It is needed to start as 0.
    Attributes:
        VALIDITY_MASK (int): Represents a valid mask channel, typically used to indicate valid grid positions.
        validity_mask (int): do not make sense. The restritions can overbound the grid. channel 0 will
        be used to indicate the map, like rio de janeiro city boundaries. a better name would be city_mask.
        RESTRICTION (auto): Represents a restriction, used to specify restricted areas or conditions on the grid.
    """
    CITY_MASK = 0
    RESTRICTION = auto()