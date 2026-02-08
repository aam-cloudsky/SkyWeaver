from typing import Tuple

from skyweaver.units.grid.geometry.hexcoord import HexCoord


def lerp(a: HexCoord, b: HexCoord, t: float) -> tuple[float, float]:
    diff = b - a
    q = a.q + diff.q * t
    r = a.r + diff.r * t
    return q, r


def hex_round(q: float, r: float) -> HexCoord:
    s = -q - r
    rq, rr, rs = round(q), round(r), round(s)

    dq = abs(rq - q)
    dr = abs(rr - r)
    ds = abs(rs - s)

    if dq > dr and dq > ds:
        rq = -rr - rs
    elif dr > ds:
        rr = -rq - rs

    return HexCoord(rq, rr)


def hex_sample(a: HexCoord, b: HexCoord, t: float) -> HexCoord:
    q, r = lerp(a, b, t)
    return hex_round(q, r)


def pointy_hex_to_pixel(hex: HexCoord, size: float) -> Tuple[float, float]:
    x = (3**0.5) * hex.q + ((3**0.5) * hex.r / 2)
    y = 3 / 2 * hex.r
    return size * x, size * y


def pixel_to_pointy_hex(x: float, y: float, size: float) -> HexCoord:
    q = ((3**0.5) / 3 * x - (1 / 3) * y) / size
    r = (2 / 3 * y) / size
    return hex_round(q, r)


def pixel_to_pointy_hex_frac(x: float, y: float, size: float) -> tuple[float, float]:
    q = ((3**0.5) / 3 * x - (1 / 3) * y) / size
    r = (2 / 3 * y) / size
    return q, r
