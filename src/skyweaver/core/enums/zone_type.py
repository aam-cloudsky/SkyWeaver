# src/skyweaver/core/enums/zone_type.py
from enum import Enum, auto


class ZoneType(Enum):
    """Defines the main types of spatial zones in the airspace."""
    UAV = auto()                  # UAV operational zone
    MAV = auto()                   # Manned aircraft zone (helicopter, air taxi)


    def __str__(self) -> str:
        """User-friendly representation."""
        return self.name