"""What each intent changes, decided from the current values of the flow.

Each function reads a Reed snapshot and returns the new value to feed, or
`None` when the intent is rejected (nothing is fed and nothing recomputes).
The rules are those of the handlers before the migration to Reed:

- add a vertiport: the cell exists, holds no heliport, no vertiport, and is
  not restricted;
- remove a vertiport: the cell exists and holds a vertiport;
- toggle a restriction: the cell exists and holds no heliport and no
  vertiport.
"""

from __future__ import annotations

from typing import Optional

import geopandas as gpd
from shapely.geometry import Point

from skyweaver.model import (
    HeliportCells,
    RestrictedCells,
    RestrictionToggles,
    VertiportEdit,
    VertiportEdits,
    Vertiports,
)
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.hexgrid.geometry.hexcoord import HexCoord
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid


def locate(snapshot, latitude: float, longitude: float) -> Optional[HexCoord]:
    """The grid cell under a WGS84 point, or `None` outside the grid."""

    domain: Domain = snapshot[Domain]
    grid: HexGrid = snapshot[HexGrid]
    geo = gpd.GeoDataFrame(geometry=[Point(longitude, latitude)], crs="EPSG:4326")
    cell = grid.get_cell_from_cartesian(domain.to_local(geo)[0])
    return None if cell is None else cell.coord


def vertiport_coords(snapshot) -> set[HexCoord]:
    grid: HexGrid = snapshot[HexGrid]
    vertiports: Vertiports = snapshot[Vertiports]
    return {cell.coord for cell in grid.get_cell_from_cartesians(vertiports.points)}


def add_vertiport(snapshot, latitude: float, longitude: float) -> Optional[VertiportEdits]:
    coord = locate(snapshot, latitude, longitude)
    if coord is None:
        return None
    if coord in snapshot[HeliportCells].coords:
        return None
    if coord in vertiport_coords(snapshot):
        return None
    if coord in snapshot[RestrictedCells].coords:
        return None
    edits: VertiportEdits = snapshot[VertiportEdits]
    return edits.appended(VertiportEdit("add", coord))


def remove_vertiport(
    snapshot, latitude: float, longitude: float
) -> Optional[VertiportEdits]:
    coord = locate(snapshot, latitude, longitude)
    if coord is None or coord not in vertiport_coords(snapshot):
        return None
    edits: VertiportEdits = snapshot[VertiportEdits]
    return edits.appended(VertiportEdit("remove", coord))


def toggle_restriction(
    snapshot, latitude: float, longitude: float
) -> Optional[RestrictionToggles]:
    coord = locate(snapshot, latitude, longitude)
    if coord is None:
        return None
    if coord in snapshot[HeliportCells].coords:
        return None
    if coord in vertiport_coords(snapshot):
        return None
    toggles: RestrictionToggles = snapshot[RestrictionToggles]
    return toggles.toggled(coord)
