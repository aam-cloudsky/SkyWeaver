from typing import Iterable
from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.grid.hexgrid.hexgrid import HexGrid
from skyweaver.planning.search_space.search_space import SearchSpace
from skyweaver.discretization.grid.hexgrid.hextopology import neighbors


class HexGridSearchSpace(SearchSpace):
    def __init__(self, grid: HexGrid):
        self.grid = grid

    def successors(self, coord: HexCoord) -> Iterable[HexCoord]:
        succ = []
        for n in neighbors(coord):
            cell = self.grid._get_cell_from_coord(n)
            if cell and cell.navigable:
                succ.append(n)
        return succ

    def heuristic(self, a: HexCoord, b: HexCoord) -> float:
        return (a - b).norm()
