from abc import ABC, abstractmethod
from shapely.geometry import Point, Polygon


class BaseCell(ABC):
    """
    Abstract base class for any discretized cell.
    """

    @property
    @abstractmethod
    def cost(self) -> float:
        """Traversal cost of this cell."""
        pass

    @property
    @abstractmethod
    def navigable(self) -> bool:
        """Whether this cell is traversable."""
        pass

    @property
    @abstractmethod
    def size(self) -> float:
        """Characteristic size of the cell."""
        pass

    @property
    @abstractmethod
    def polygon(self) -> Polygon:
        """Geometric footprint of the cell."""
        pass

    @property
    @abstractmethod
    def cartesian_center(self) -> Point:
        """Center of the cell in world coordinates."""
        pass
