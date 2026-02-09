from typing import List, Optional

from shapely import Point
from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.grid.geometry.basecell import BaseCell

from skyweaver.units.routes.graph.graph_builder import GraphBuilder
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost
from skyweaver.units.routes.routing import Routing, compute_terminal_paths


# TODO: The class Routing seems a bit odd, once it
# Routes Unit is already called route.
# Maybe it should be renamed to something like RoutePlanner or RouteCalculator,
# to avoid confusion with the unit name and to better reflect its purpose.
class RoutesUnit(OperationalUnit[RoutesOutpost]):
    def __init__(self, outpost: Optional[RoutesOutpost] = None):

        if outpost is None:
            outpost = RoutesOutpost()
        super().__init__(outpost=outpost)

        print(
            "[RoutesUnit] TODO: Cluster Parcel Should be a Optional Consumed Parcel, therefore, 'CONSUMED' is not the right role"
        )

        self.builder = GraphBuilder(outpost=self._outpost)
        self.airspace_graph = self.builder.build_airspace_graph()

        self.planner = Routing(self.airspace_graph)

        with self._outpost:
            self._outpost.routes_parcel.airspace_graph = self.airspace_graph

        self._terminals: List[BaseCell] = self._get_terminals()

    def add_terminal(self, cell: BaseCell) -> None:
        if cell not in self._terminals:
            self._terminals.append(cell)

    def remove_terminal(self, cell: BaseCell) -> None:
        if cell in self._terminals:
            self._terminals.remove(cell)

    def clear_terminals(self) -> None:
        self._terminals.clear()

    def _get_terminals(self) -> List[BaseCell]:
        # combine local terminals with terminals from vertiports
        if hasattr(self, "_terminals") and self._terminals:
            terminals = list(self._terminals)
        else:
            terminals = []

        vertiports = self._outpost.vertiports_parcel.vertiports
        grid = self._outpost.grid_parcel.grid
        for vertiport in vertiports:
            cell = grid.get_cell_from_cartesian(vertiport.x, vertiport.y)
            if cell and cell not in terminals:
                terminals.append(cell)

        return terminals

    def run(self) -> None:

        terminals = self._get_terminals()

        paths: List[List[BaseCell]] = compute_terminal_paths(self.planner, terminals)

        routes_graph = self.builder.build_routes_graph(paths)
        terminals_graph = self.builder.build_terminals_graph(paths)

        with self._outpost:
            self._outpost.routes_parcel.routes_graph = routes_graph
            self._outpost.routes_parcel.terminals_graph = terminals_graph

    def is_cell_on_route(self, cell: BaseCell) -> bool:
        routes_graph = self._outpost.routes_parcel.routes_graph
        if routes_graph is None:
            return False
        paths = routes_graph.paths
        for path in paths:
            if cell in path:
                return True
        return False

    def rebuild_airspace_graph(self) -> None:
        self.airspace_graph = self.builder.build_airspace_graph()
        self.planner = Routing(self.airspace_graph)
        with self._outpost:
            self._outpost.routes_parcel.airspace_graph = self.airspace_graph
