from skyweaver.discretization.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.hexgrid.hexgrid import HexGrid
from skyweaver.discretization.hexgrid.hextopology import neighbors


class HexGridPathAdapter:
    def __init__(self, grid: HexGrid):
        self.grid = grid

    # FOR A*
    def successors(self, coord: HexCoord) -> list[HexCoord]:
        """
        Return navigable neighboring coordinates for A* expansion.
        """
        succ = []
        for n in neighbors(coord):
            cell = self.grid.get_cell(n)
            if cell is None:
                continue
            if not cell.navigable:
                continue
            succ.append(n)
        return succ

    def heuristic(self, a: HexCoord, b: HexCoord) -> float:
        return (a-b).norm()