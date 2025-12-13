from typing import List
from skyweaver.discretization.hexgrid.hexcoord import HexCoord

__all__ = [
    "DIRECTIONS",
    "DIAGONALS",
    "neighbors",
    "hex_ring",
    "all_hexes_in_range",
    "hex_reachable_in_steps",
]


# --- Constants -------------------------------------------------

DIRECTIONS: tuple[HexCoord, ...] = (
    HexCoord(1, 0),
    HexCoord(1, -1),
    HexCoord(0, -1),
    HexCoord(-1, 0),
    HexCoord(-1, 1),
    HexCoord(0, 1),
)

DIAGONALS: tuple[HexCoord, ...] = tuple(
    DIRECTIONS[i] + DIRECTIONS[(i + 1) % 6]
    for i in range(6)
)


# --- Topology functions ---------------------------------------

def axial_direction(direction_index: int) -> HexCoord:
    return DIRECTIONS[direction_index]


def axial_neighbor(coord: HexCoord, direction_index: int) -> HexCoord:
    return coord + DIRECTIONS[direction_index]


def neighbors(coord: HexCoord) -> List[HexCoord]:
    return [coord + d for d in DIRECTIONS]


def hex_ring(center: HexCoord, radius: int) -> List[HexCoord]:
    if radius == 0:
        return [center]

    results = []
    hex = center + DIRECTIONS[4] * radius

    for direction in range(6):
        for _ in range(radius):
            results.append(hex)
            hex = axial_neighbor(hex, direction)

    return results


def all_hexes_in_range(center: HexCoord, range_distance: int) -> List[HexCoord]:
    results = []
    for q in range(-range_distance, range_distance + 1):
        r1 = max(-range_distance, -q - range_distance)
        r2 = min(range_distance, -q + range_distance)
        for r in range(r1, r2 + 1):
            results.append(center + HexCoord(q, r))
    return results


def intersecting_ranges(
    center_a: HexCoord,
    range_a: int,
    center_b: HexCoord,
    range_b: int,
) -> List[HexCoord]:
    return [
        h for h in all_hexes_in_range(center_a, range_a)
        if (h - center_b).norm() <= range_b
    ]


def hex_reachable_in_steps(start: HexCoord, steps: int) -> List[HexCoord]:
    reachable = set()
    for q in range(-steps, steps + 1):
        r1 = max(-steps, -q - steps)
        r2 = min(steps, -q + steps)
        for r in range(r1, r2 + 1):
            reachable.add(start + HexCoord(q, r))
    return list(reachable)
