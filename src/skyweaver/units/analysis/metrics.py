from __future__ import annotations
from collections import Counter

from skyweaver.units.routes.graph.graph_pack import (
    AirspaceGraphPack,
    RoutesGraphPack,
    TerminalsGraphPack,
)
from .base import APLResult, BetweennessResult
from .registry import register


@register("apl")
def average_path_length(
    g0: AirspaceGraphPack,
    g1: RoutesGraphPack,
    g2: TerminalsGraphPack,
) -> APLResult:
    if g2.vcount() == 0:
        return APLResult(name="apl", value=0.0)

    apl = g2.graph.average_path_length(weights="weight", unconn=True)
    value = float(apl) if apl is not None else 0.0
    return APLResult(name="apl", value=value)


@register("betweenness")
def betweenness(
    g0: AirspaceGraphPack,
    g1: RoutesGraphPack,
    g2: TerminalsGraphPack,
) -> BetweennessResult:
    if g1.vcount() == 0:
        return BetweennessResult(name="betweenness", values={})

    paths = g1.paths
    if not paths:
        return BetweennessResult(name="betweenness", values={})

    centrality = Counter()
    for path in paths:
        if len(path) <= 2:
            continue
        for cell_mid in path[1:-1]:
            centrality[cell_mid] += 1

    if not centrality:
        return BetweennessResult(name="betweenness", values={})

    return BetweennessResult(name="betweenness", values=dict(centrality))
