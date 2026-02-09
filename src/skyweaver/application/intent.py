from dataclasses import dataclass

from skyweaver.units.grid.geometry.hexcoord import HexCoord


class HexIntent:
    pass


@dataclass(frozen=True)
class ToggleRestriction(HexIntent):
    coord: HexCoord


@dataclass(frozen=True)
class BeginDragTerminal(HexIntent):
    coord: HexCoord


@dataclass(frozen=True)
class EndDragTerminal(HexIntent):
    start: HexCoord
    end: HexCoord
