from __future__ import annotations
from collections import Counter
from typing import Dict

from skyweaver.units.hexgrid.structure.hexcell import HexCell
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
) -> Dict[HexCell, int]:

    if g1.vcount() == 0:
        return {}

    graph = g1.graph

    centrality = Counter()

    vertices = list(range(graph.vcount()))

    for i, source in enumerate(vertices):

        for target in vertices[i + 1 :]:

            vpaths = graph.get_shortest_paths(
                source,
                to=target,
                output="vpath",
            )

            if not vpaths or not vpaths[0]:
                continue

            vpath = vpaths[0]

            if len(vpath) <= 2:
                continue

            for vid in vpath[1:-1]:

                cell = g1.get_cell(vid)

                if cell is not None:
                    centrality[cell] += 1

    return dict(centrality)
