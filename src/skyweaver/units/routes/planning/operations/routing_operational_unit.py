from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Tuple

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.grid.geometry.basecell import BaseCell
from skyweaver.planning.graph.graph_builder import GraphBuilder
from skyweaver.planning.logistics.planning_outpost import PlanningOutpost
from skyweaver.planning.routing import Routing, compute_terminal_paths


class RoutingOperationalUnit(OperationalUnit):
    def __init__(self, outpost: PlanningOutpost, terminals: Iterable[BaseCell]):
        super().__init__(outpost)
        self._terminals = list(terminals)

    def run(self) -> None:
        airspace = self.outpost.planning_parcel.airspace_graph
        if airspace is None:
            return

        planner = Routing(airspace.graph)

        paths = compute_terminal_paths(planner, self._terminals)
        paths_with_cost: List[Tuple[List[BaseCell], float]] = []

        for a, b in combinations(self._terminals, 2):
            if a not in planner.cell_to_vid or b not in planner.cell_to_vid:
                continue
            cost, cells = planner.shortest_path(a, b)
            if cells is not None:
                paths_with_cost.append((cells, cost))

        builder = GraphBuilder(outpost=self.outpost)
        routes = builder.build_routes_graph(paths)
        terminals = builder.build_terminals_graph(paths_with_cost)

        with self.outpost:
            self.outpost.planning_parcel.routes_graph = routes
            self.outpost.planning_parcel.terminals_graph = terminals
