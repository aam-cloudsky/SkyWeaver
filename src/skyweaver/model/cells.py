"""Sets of hexagonal cells: where heliports are and what is restricted."""

from __future__ import annotations

from dataclasses import dataclass

from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord


@dataclass(frozen=True)
class HeliportCells:
    """The coordinates of the cells that contain a heliport."""

    coords: frozenset[HexCoord] = frozenset()


@dataclass(frozen=True)
class RestrictionToggles:
    """The coordinates of the cells the user restricted."""

    coords: frozenset[HexCoord] = frozenset()

    def toggled(self, coord: HexCoord) -> RestrictionToggles:
        """Restrict `coord` if it is free, free it if it is restricted."""

        return RestrictionToggles(self.coords ^ {coord})


@dataclass(frozen=True)
class RestrictedCells:
    """The coordinates of the cells no route may cross."""

    coords: frozenset[HexCoord] = frozenset()
