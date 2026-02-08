from abc import ABC, abstractmethod
from shapely.geometry import Point, Polygon

class BaseCell(ABC):
    """
    Abstract base class for any discretized cell.
    """

    def __init__(self, size: float = 1.0, available: bool = True, cost: float = 1.0):
        self._available: bool = available
        self._cost: float = cost
        self._size = size  # Default size; override in subclasses

    @property
    def available(self) -> bool:
        return self._available
    
    @property
    def size(self) -> float:
        return self._size
    
    @property
    def cost(self) -> float:
        if not self._available:
            return float("inf")
        return self._cost
    
    @property
    def polygon(self) -> Polygon:
        """Return the shapely Polygon representing the hex cell in 2D space."""
        if not hasattr(self, '_polygon'):
            self._polygon = self._create_polygon()
        return self._polygon
    
    @property
    def cartesian_center(self) -> Point:
        if not hasattr(self, "_cartesian_center"):
            self._cartesian_center = self._compute_cartesian_center()
        return self._cartesian_center
    
    def set_unavailable(self):
        self._available = False

    def set_available(self):
        self._available = True
    
    
    def __hash__(self):
        return id(self)

    def set_cost(self, cost: float) -> None:
        if cost < 0:
            raise ValueError("Cost must be non-negative")
        self._cost = cost

    def set_availability(self, available: bool) -> None:
        if self._available != available:
            self._available = available

    @abstractmethod
    def _compute_cartesian_center(self) -> Point:
        pass
    
    @abstractmethod
    def _create_polygon(self) -> Polygon:
        """Center of the cell in world coordinates."""
        pass
