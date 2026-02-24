from typing import Generator, List

from skyweaver.units.hexgrid.geometry.axial_bounds import AxialBounds
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord


class HexTopology:
    """
    Provides functions for hexagonal grid topology, such as finding neighbors, rings, and distances.
    These functions operate on axial coordinates (q, r) and are independent of the specific grid implementation.
    """

    def __init__(self):

        self.DIRECTIONS: tuple[HexCoord, ...] = (
            HexCoord(1, 0),
            HexCoord(1, -1),
            HexCoord(0, -1),
            HexCoord(-1, 0),
            HexCoord(-1, 1),
            HexCoord(0, 1),
        )

        self.DIAGONALS: tuple[HexCoord, ...] = tuple(
            self.DIRECTIONS[i] + self.DIRECTIONS[(i + 1) % 6] for i in range(6)
        )

    # --- Topology functions ---------------------------------------

    def axial_direction(self, direction_index: int) -> HexCoord:
        return self.DIRECTIONS[direction_index]

    def axial_neighbor(self, coord: HexCoord, direction_index: int) -> HexCoord:
        return coord + self.DIRECTIONS[direction_index]

    def neighbors(self, coord: HexCoord) -> List[HexCoord]:
        return [coord + d for d in self.DIRECTIONS]

    def hex_ring(self, center: HexCoord, radius: int) -> List[HexCoord]:
        if radius == 0:
            return [center]

        results = []
        hex = center + self.DIRECTIONS[4] * radius

        for direction in range(6):
            for _ in range(radius):
                results.append(hex)
                hex = self.axial_neighbor(hex, direction)

        return results

    @classmethod
    def all_coords_in_range(
        cls, center: HexCoord, range_distance: int
    ) -> Generator[HexCoord, None, None]:
        bounds = AxialBounds(
            min_q=-range_distance,
            max_q=range_distance,
            min_r=-range_distance,
            max_r=range_distance,
        )

        for offset in bounds.iter_coords():
            if offset.norm() > range_distance:
                continue

            yield center + offset

    @classmethod
    def intersecting_ranges(
        cls,
        center_a: HexCoord,
        range_a: int,
        center_b: HexCoord,
        range_b: int,
    ) -> List[HexCoord]:
        return [
            coord
            for coord in cls.all_coords_in_range(center_a, range_a)
            if (coord - center_b).in_radius(range_b)
        ]

    @classmethod
    def hex_reachable_in_steps(
        cls, start: HexCoord, steps: int
    ) -> Generator[HexCoord, None, None]:
        yield from cls.all_coords_in_range(start, steps)

    @classmethod
    def hex_distance(cls, a: HexCoord, b: HexCoord) -> int:
        return (a - b).norm()
