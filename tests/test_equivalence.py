"""On the Rio de Janeiro data, each flow function equals the old units.

The old units run through `RuntimeUnits` exactly as the old runtime
bootstraps them; the flow functions run from the configuration path on
their own. This file goes away with the old core.
"""

from __future__ import annotations

import pytest

from conftest import CONFIG_PATH, xy
from skyweaver.model import RestrictionToggles
from skyweaver.units.restriction.restrictions import restrict_cells
from skyweaver.units.routes.graph.graph_pack import GraphPack
from skyweaver.units.routes.route_computation import build_airspace_graph


@pytest.fixture(scope="module")
def old_runtime():
    from skyweaver.application.runtime.application_runtime import ApplicationRuntime
    from skyweaver.core.logistics.depot import Depot

    Depot()
    return ApplicationRuntime(config_path=str(CONFIG_PATH))


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
