"""The routes between the vertiports."""

from __future__ import annotations

from dataclasses import dataclass, field

from skyweaver.units.routes.graph.graph_pack import RoutesGraphPack, TerminalsGraphPack


@dataclass(frozen=True)
class Routes:
    """The routes graph (cells and paths) and the terminals graph.

    The igraph graphs inside the packs are built once by `compute_routes`
    and only read afterwards.
    """

    routes_graph: RoutesGraphPack = field(default_factory=RoutesGraphPack)
    terminals_graph: TerminalsGraphPack = field(default_factory=TerminalsGraphPack)
