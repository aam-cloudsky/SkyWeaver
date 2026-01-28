

from abc import abstractmethod
from typing import Any, Iterable, List, Tuple

from skyweaver.grid.geometry.basecell import BaseCell
from skyweaver.grid.structure.basegrid import BaseGrid



class NullGrid(BaseGrid):

 
    def iter_domain_cells(self) -> Iterable[BaseCell]:
        """Materialize the whole grid for visualization/debugging"""
        return []

    def get_cell_from_cartesian(self, x: float, y: float) -> Any:
        """Get the cell at given cartesian coordinates"""
        return None


  
    def get_domain(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Get the cell at given cartesian coordinates"""
        return ((0.0, 0.0), (0.0, 0.0))
 

    def neighbors(self, cell: BaseCell) -> List[BaseCell]:
        """Get the neighboring cells of a given cell"""
        return []
   


    def lower_bound_steps(self, a: BaseCell, b: BaseCell) -> float:
        """Estimate the minimum number of steps between two cells"""
        return 1  # Default implementation; override in subclasses
