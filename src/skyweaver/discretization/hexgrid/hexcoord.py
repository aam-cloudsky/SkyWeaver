from dataclasses import dataclass


@dataclass(frozen=True)
class HexCoord():
    """
    Axial Coordinates for Hexagonal Grids.
    See https://www.redblobgames.com/grids/hexagons/#coordinates-axial
    """

    q: int
    r: int
    
    @property
    def s(self) -> int:
        """
        HexCoordinate third coordinate.
        The constraint is that q + r + s = 0.
        """
        return -self.q - self.r
    
    def __add__(self, other: "HexCoord") -> "HexCoord":
        if not isinstance(other, HexCoord):
            return NotImplemented
        return HexCoord(self.q + other.q, self.r + other.r)

    def __sub__(self, other: "HexCoord") -> "HexCoord":
        if not isinstance(other, HexCoord):
            return NotImplemented
        return HexCoord(self.q - other.q, self.r - other.r)
    
    def __mul__(self, k: int) -> "HexCoord":
        if not isinstance(k, int):
            return NotImplemented
        return HexCoord(self.q * k, self.r * k)

    def __rmul__(self, k: int) -> "HexCoord":
        return self.__mul__(k)

    def norm(self) -> int:
        """
        Hex lattice norm (cube L1 metric).
        Integer-valued. Not Euclidean.
        """
        return max(abs(self.q), abs(self.r), abs(self.q + self.r))