from typing import List
from skyweaver.discretization.grid.base_cell import BaseCell
from skyweaver.discretization.grid.base_grid import BaseGrid


class NullGrid(BaseGrid):
    def iter_domain_cells(self):
        return iter([])

    def get_cell_from_cartesian(self, x, y):
        raise RuntimeError("Grid not initialized")

    def get_domain(self):
        raise RuntimeError("Grid not initialized")

    def neighbors(self, cell: BaseCell) -> List[BaseCell]:
        """Get the neighboring cells of a given cell"""

        return []
    
    def lower_bound_steps(self, a: BaseCell, b: BaseCell) -> float:
        """Estimate the minimum number of steps between two cells"""
        return float("inf")  # Default implementation; override in subclasses