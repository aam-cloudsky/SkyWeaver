import math
from typing import Iterable, List

from itertools import combinations
import igraph as ig

from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.routes.graph.graph_pack import AirspaceGraphPack
from skyweaver.units.routes.routing import Routing


def _require_parameter(info: dict, key: str):
    if key not in info:
        raise ValueError(f"Missing required parameter '{key}' for connectivity mode.")

    return info[key]


def _terminal_distance(a: HexCell, b: HexCell) -> float:
    return (a.coord - b.coord).norm()


def _build_single_linkage_hac_pairs(
    terminals: list[HexCell],
) -> set[tuple[HexCell, HexCell]]:

    if len(terminals) <= 1:
        return set()

    graph = ig.Graph()
    graph.add_vertices(len(terminals))

    weights: list[float] = []
    edges: list[tuple[int, int]] = []

    for i in range(len(terminals)):
        for j in range(i + 1, len(terminals)):

            a = terminals[i]
            b = terminals[j]

            distance = _terminal_distance(a, b)

            edges.append((i, j))
            weights.append(distance)

    graph.add_edges(edges)

    mst = graph.spanning_tree(weights=weights)

    pairs: set[tuple[HexCell, HexCell]] = set()

    for edge in mst.es:
        u, v = edge.tuple

        a = terminals[u]
        b = terminals[v]

        pair = (a, b) if id(a) < id(b) else (b, a)
        pairs.add(pair)

    return pairs


def _build_pairs(
    terminals: list[HexCell],
    connectivity_mode: str,
    info: dict,
) -> set[tuple[HexCell, HexCell]]:

    if connectivity_mode == "all_pairs":
        return set(combinations(terminals, 2))

    elif connectivity_mode == "knn":

        k = _require_parameter(info, "k")

        return Routing.build_knn_pairs(
            terminals,
            k,
        )

    elif connectivity_mode == "Single-Linkage_HAC":
        return _build_single_linkage_hac_pairs(
            terminals,
        )

    else:
        raise ValueError(f"Unknown connectivity_mode: {connectivity_mode}")


def interconnect(
    terminals: Iterable[HexCell],
    airspace_graph: AirspaceGraphPack,
    connectivity_mode: str,
    info: dict,
) -> List[List[HexCell]]:
    """
    Compute shortest paths between all terminal (AirspaceGraphPack G0 → paths).

    Returns:
        List of paths (each path is a list of HexCell)
    """

    pairs = _build_pairs(
        list(terminals),
        connectivity_mode,
        info,
    )

    paths = _build_paths(pairs=pairs, airspace_graph=airspace_graph)

    return paths


def _build_paths(
    pairs: set[tuple[HexCell, HexCell]],
    airspace_graph: AirspaceGraphPack,
):

    paths: List[List[HexCell]] = []
    weights: list[float] = Routing.obtain_edges_weights(airspace_graph)

    for a, b in pairs:
        if a not in airspace_graph._cell_to_vid or b not in airspace_graph._cell_to_vid:
            continue

        cost, cells = Routing.shortest_path(airspace_graph, a, b, weights)

        # to make sure invalid path will not to propagate
        if cells is not None and not math.isinf(cost):
            paths.append(cells)

    return paths
