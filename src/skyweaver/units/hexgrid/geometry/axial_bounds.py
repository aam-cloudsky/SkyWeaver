from dataclasses import dataclass
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord
from typing import Generator


@dataclass(frozen=True)
class AxialBounds:
    min_q: int
    max_q: int
    min_r: int
    max_r: int

    def iter_coords(self) -> Generator[HexCoord, None, None]:
        for q in range(self.min_q, self.max_q + 1):
            for r in range(self.min_r, self.max_r + 1):
                yield HexCoord(q, r)
