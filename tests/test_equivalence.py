"""On the Rio de Janeiro data, each flow function equals the old units.

The old units run through `RuntimeUnits` in the order of the old runtime's
bootstrap, with its vertiport conflict filter (copied below from
`cd02743`); the flow functions run from the configuration path on their
own. This file goes away with the old core.
"""

from __future__ import annotations

import pytest

from conftest import CONFIG_PATH, xy
from skyweaver.model import RestrictionToggles
from skyweaver.units.restriction.restrictions import restrict_cells
from skyweaver.units.routes.graph.graph_pack import GraphPack
from skyweaver.units.routes.route_computation import build_airspace_graph


class OldRuntime:
    """The bootstrap of the old ApplicationRuntime at cd02743."""

    def __init__(self, config_path: str) -> None:
        from skyweaver.application.runtime.runtime_units import RuntimeUnits

        self.units = RuntimeUnits(config_path)
        self.units.yaml.run()
        self.units.sources.run()
        self.units.domain.run()
        self.units.alignment.run()
        self.units.grid.run()
        self._remove_vertiport_heliport_conflicts()
        self.units.restriction.run()
        self.units.routes.run()

    def _remove_vertiport_heliport_conflicts(self) -> None:
        grid = self.units.grid._outpost.grid_parcel.grid
        heliports = self.units.alignment._outpost.heliports_parcel.heliports
        vertiports = self.units.alignment._outpost.vertiports_parcel.vertiports
        heliport_cells = set(grid.get_cell_from_cartesians(heliports))
        filtered = []
        for point in vertiports:
            cell = grid.get_cell_from_cartesian(point)
            if cell is None or cell in heliport_cells:
                continue
            filtered.append(point)
        with self.units.alignment._outpost:
            self.units.alignment._outpost.vertiports_parcel.vertiports = filtered


@pytest.fixture(scope="module")
def old_runtime():
    from skyweaver.core.logistics.depot import Depot

    Depot()
    return OldRuntime(str(CONFIG_PATH))


def edges(pack: GraphPack) -> set[frozenset]:
    graph = pack.ig_graph
    return {
        frozenset((pack.get_cell(e.source).coord, pack.get_cell(e.target).coord))
        for e in graph.es
    }


def test_configuration(rio, old_runtime) -> None:
    parcel = old_runtime.units.yaml._outpost.yaml_parcel
    assert dict(rio.configuration.fields) == parcel.yaml_fields
    assert rio.configuration.config_dir == parcel.config_dir


def test_alignment_split(rio, old_runtime) -> None:
    assert xy(rio.heliports.points) == xy(
        old_runtime.units.alignment._outpost.heliports_parcel.heliports
    )
    assert len(rio.candidates.points) == len(rio.geodata.vertiports)


def test_filter(rio, old_runtime) -> None:
    old = old_runtime.units.routes._outpost.vertiports_parcel.vertiports
    assert xy(rio.base.points) == xy(old)
    assert len(rio.base.points) == len(rio.candidates.points) - 1


def test_airspace_graph(rio, old_runtime) -> None:
    old = old_runtime.units.routes._outpost.routes_parcel.airspace_graph
    new = build_airspace_graph(
        rio.grid(), restrict_cells(rio.heliport_cells, RestrictionToggles())
    )
    assert new.vcount() == old.vcount()
    assert edges(new) == edges(old)
