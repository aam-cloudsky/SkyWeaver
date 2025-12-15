from abc import ABC, abstractmethod
from typing import Any, Iterable, List, Tuple

from skyweaver.discretization.grid.base_cell import BaseCell


class BaseGrid(ABC):
    @abstractmethod
    def successors(self, node: Any) -> list[Any]:
        """Get neighbors (successors) for A* expansion"""
        pass

    @abstractmethod
    def heuristic(self, a: Any, b: Any) -> float:
        """Calculate heuristic for A*"""
        pass

    @abstractmethod
    def iter_domain_cells(self) -> Iterable[BaseCell]:
        """Materialize the whole grid for visualization/debugging"""
        pass


    @abstractmethod
    def get_cell_from_cartesian(self, x: float, y: float) -> Any:
        """Get the cell at given cartesian coordinates"""
        pass

    @abstractmethod
    def get_domain(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get the cell at given cartesian coordinates"""
        pass
