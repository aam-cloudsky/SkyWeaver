from __future__ import annotations
from collections import Counter
from typing import Dict

from skyweaver.units.grid.geometry.basecell import BaseCell
from skyweaver.units.routes.graph.graph_pack import (
    RoutesGraphPack,
)


def average_path_length(
    g1: RoutesGraphPack,
) -> float:
    if g1.vcount() == 0:
        return 0.0

    paths = g1.paths
    lengths = [len(path) - 1 for path in paths]
    print("path lengths:", lengths)
    print("APL:", sum(lengths) / len(lengths))

    if not lengths:
        return 0.0
    return sum(lengths) / len(lengths)


def betweenness(
    g1: RoutesGraphPack,
) -> Dict[BaseCell, int]:
    if g1.vcount() == 0:
        return {}

    paths = g1.paths
    if not paths:
        return {}

    centrality = Counter()
    for path in paths:
        if len(path) <= 2:
            continue
        for cell_mid in path[1:-1]:
            centrality[cell_mid] += 1

    if not centrality:
        return {}

    return dict(centrality)
