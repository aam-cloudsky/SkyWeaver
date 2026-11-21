"""Heliports and vertiports, from the source data to the current list."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from geopandas import GeoDataFrame
from shapely.geometry import Point

from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord


@dataclass(frozen=True)
class SourceGeoData:
    """Heliports and candidate vertiports as read from the data files.

    The frames are mutable objects; no function changes them after they are
    committed.
    """

    heliports: GeoDataFrame
    vertiports: GeoDataFrame


@dataclass(frozen=True)
class Heliports:
    """Heliports in the local frame of the domain."""

    points: tuple[Point, ...] = ()


@dataclass(frozen=True)
class CandidateVertiports:
    """Vertiports from the data, in the local frame of the domain."""

    points: tuple[Point, ...] = ()


@dataclass(frozen=True)
class BaseVertiports:
    """Candidate vertiports whose cell exists and holds no heliport."""

    points: tuple[Point, ...] = ()


@dataclass(frozen=True)
class Vertiports:
    """The current vertiports: the base list with the user's edits applied."""

    points: tuple[Point, ...] = ()


@dataclass(frozen=True)
class VertiportEdit:
    """One edit of the vertiport list made by the user.

    `add` appends the center of the cell `coord`; `remove` drops every
    vertiport whose cell is `coord`.
    """

    kind: Literal["add", "remove"]
    coord: HexCoord

    def __post_init__(self) -> None:
        if self.kind not in ("add", "remove"):
            raise ValueError(f"unknown vertiport edit kind: {self.kind!r}")


@dataclass(frozen=True)
class VertiportEdits:
    """The ordered log of the user's vertiport edits.

    Provisional: it reproduces the add and remove intents of this version.
    The scenario editor replaces it with the scenario document.
    """

    edits: tuple[VertiportEdit, ...] = ()

    def appended(self, edit: VertiportEdit) -> VertiportEdits:
        return VertiportEdits(self.edits + (edit,))
