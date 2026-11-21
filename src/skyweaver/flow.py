"""SkyWeaver's computation as a Reed flow.

Thirteen functions, each producing one value type (see `skyweaver.model`).
Reed runs a function when its inputs change and commits what it returns; the
scene the frontend draws is the last value of the chain.

    ConfigPath ─▶ Configuration ─▶ SourceGeoData ─▶ Domain ─▶ HexGrid
                                         │             │
                     Heliports ◀─────────┴─────────────┤
                     CandidateVertiports ◀─────────────┘
    Heliports + HexGrid ─▶ HeliportCells
    CandidateVertiports + HeliportCells + HexGrid ─▶ BaseVertiports
    BaseVertiports + VertiportEdits (fed) + HexGrid ─▶ Vertiports
    HeliportCells + RestrictionToggles (fed) ─▶ RestrictedCells
    HexGrid + RestrictedCells ─▶ AirspaceGraphPack
    AirspaceGraphPack + Vertiports + HexGrid + Configuration ─▶ Routes
    Domain + Heliports + Vertiports + Routes + HexGrid ─▶ SceneSnapshot

Trigger policies. Reed's default, `ALL_INPUTS_CHANGED`, fires a node again
only when every input changed since its last firing. The nodes that must
react to a single changed input (an edit, a toggle, or what follows from
them) declare `ANY_INPUT_CHANGED`.

Startup feeds `ConfigPath`, an empty `VertiportEdits` and an empty
`RestrictionToggles`; afterwards the intent handlers feed new
`VertiportEdits` and `RestrictionToggles` values.
"""

from __future__ import annotations

from pathlib import Path

from reed import Flow, Session, TriggerPolicy

from skyweaver.application.runtime.materialization.scene_materializer import (
    materialize_scene,
)
from skyweaver.model import ConfigPath, RestrictionToggles, VertiportEdits
from skyweaver.units.domain.domain_construction import build_domain
from skyweaver.units.geodata_domain_alignment.alignment import (
    align_heliports,
    align_vertiports,
)
from skyweaver.units.hexgrid.grid_construction import build_grid
from skyweaver.units.restriction.restrictions import (
    locate_heliport_cells,
    restrict_cells,
)
from skyweaver.units.routes.route_computation import (
    build_airspace_graph,
    compute_routes,
)
from skyweaver.units.routes.vertiports import (
    apply_vertiport_edits,
    filter_candidate_vertiports,
)
from skyweaver.units.sources.geodata import load_geodata
from skyweaver.units.yaml_loader.configuration import load_configuration

ANY = TriggerPolicy.ANY_INPUT_CHANGED

# (function, trigger policy), in the order of the chain.
NODES = (
    (load_configuration, None),
    (load_geodata, None),
    (build_domain, None),
    (align_heliports, None),
    (align_vertiports, None),
    (build_grid, None),
    (locate_heliport_cells, None),
    (filter_candidate_vertiports, None),
    (apply_vertiport_edits, ANY),
    (restrict_cells, ANY),
    (build_airspace_graph, ANY),
    (compute_routes, ANY),
    (materialize_scene, ANY),
)


def build_flow() -> Flow:
    """The flow of the thirteen functions with their trigger policies."""

    flow = Flow()
    for function, policy in NODES:
        if policy is None:
            flow.add(function)
        else:
            flow.add(function, trigger_policy=policy)
    return flow


def start_session(config_path: str | Path, flow: Flow | None = None) -> Session:
    """A session fed with the configuration and no user edit, pushed once."""

    session = (flow or build_flow()).session(observability="silent")
    session.feed(ConfigPath(Path(config_path)))
    session.feed(VertiportEdits())
    session.feed(RestrictionToggles())
    session.push()
    return session
