from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord
from skyweaver.units.hexgrid.structure.hexcell_state import HexCellState


class HexCell:
    """
    This HexCell represents a single hexagonal cell in a hexagonal grid.
    It is defined by its Hex Coordinates (Axial Coordinates), size (distance from center to any vertex),

    """

    def __init__(self, coord: HexCoord, size: float, cost: float = 1.0):
        self._cost: float = cost
        self._size = size
        self._coord: HexCoord = coord

        self._state: HexCellState = HexCellState.AVAILABLE

    def __eq__(self, other):
        if not isinstance(other, HexCell):
            return NotImplemented
        return self._coord == other._coord and self._size == other._size

    def __hash__(self):
        return hash((self._coord, self._size))

    @property
    def coord(self) -> HexCoord:
        return self._coord

    @property
    def size(self) -> float:
        return self._size

    @property
    def cost(self) -> float:

        if not self.is_traversable:
            return float("inf")
        return self._cost

    def set_cost(self, cost: float) -> None:
        if cost < 0:
            raise ValueError("Cost must be non-negative")
        self._cost = cost

    # =======================================================
    # State Management
    # =======================================================
    def set_restricted(self):
        self._state = HexCellState.RESTRICTED

    def set_available(self):
        self._state = HexCellState.AVAILABLE

    @property
    def is_traversable(self) -> bool:
        return self._state is HexCellState.AVAILABLE
