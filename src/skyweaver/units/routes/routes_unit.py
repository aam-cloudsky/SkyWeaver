from typing import List, Optional

from shapely.geometry import Point

from skyweaver.core.operations.operational_unit import OperationalUnit

from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.routes.graph.graph_builder import GraphBuilder
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost
from skyweaver.units.routes.routing import Routing


class RoutesUnit(OperationalUnit[RoutesOutpost]):
    def __init__(self, outpost: Optional[RoutesOutpost] = None):

        if outpost is None:
            outpost = RoutesOutpost()
        super().__init__(outpost=outpost)

        print(
            "[RoutesUnit] TODO: Cluster Parcel Should be a Optional Consumed Parcel, therefore, 'CONSUMED' is not the right role"
        )
        self.builder = GraphBuilder(outpost=self._outpost)
        with self._outpost:

            airspace_graph = self.builder.build_airspace_graph()
            self._outpost.routes_parcel.airspace_graph = airspace_graph

        # self._terminals: List[HexCell] = self._get_terminals()

    def _from_cartesian_to_hex(self, cartesian: Point) -> Optional[HexCell]:
        grid = self._outpost.grid_parcel.grid
        return grid.get_cell_from_cartesian(cartesian)

    def _from_cell_to_cartesian(self, hex: HexCell):
        grid = self._outpost.grid_parcel.grid
        return grid.cartesian_cell_center(hex)

    def add_vertiport(self, cell: HexCell) -> None:

        if not self._is_cell_available(cell):
            return

        new_vertiport: Point = self._from_cell_to_cartesian(cell)

        with self._outpost:
            self._outpost.vertiports_parcel.vertiports.append(new_vertiport)

    def remove_vertiport(self, cell: HexCell) -> None:

        to_be_removed_vertiport = self._from_cell_to_cartesian(cell)

        if to_be_removed_vertiport not in self._outpost.vertiports_parcel.vertiports:
            return

        with self._outpost:
            self._outpost.vertiports_parcel.vertiports.remove(to_be_removed_vertiport)

    def clear_vertiports(self) -> None:
        with self._outpost:
            self._outpost.vertiports_parcel.vertiports.clear()

    def _get_vertiports(self) -> List[HexCell]:
        # combine local terminals with terminals from vertiports
        vertiports = self._outpost.vertiports_parcel.vertiports
        grid = self._outpost.grid_parcel.grid
        return grid.get_cell_from_cartesians(vertiports)

    def run(self) -> None:

        vertiports = self._get_vertiports()
        airspace_graph = self._outpost.routes_parcel.airspace_graph
        paths: List[List[HexCell]] = Routing.compute_terminal_paths(
            airspace_graph, vertiports
        )

        routes_graph = self.builder.build_routes_graph(paths)
        terminals_graph = self.builder.build_terminals_graph(paths)

        with self._outpost:
            self._outpost.routes_parcel.routes_graph = routes_graph
            self._outpost.routes_parcel.terminals_graph = terminals_graph

    # =========================================================================
    # Cells
    # =========================================================================
    def is_cell_on_route(self, cell: HexCell) -> bool:
        routes_graph = self._outpost.routes_parcel.routes_graph
        if routes_graph is None:
            return False
        paths = routes_graph.paths
        for path in paths:
            if cell in path:
                return True
        return False

    def _is_cell_available(self, cell: HexCell):
        if not cell.is_traversable:
            return False

        if self._cell_has_heliport(cell):
            return False

        return True

    def _cell_has_heliport(self, cell: HexCell) -> bool:

        grid = self._outpost.grid_parcel.grid
        heliports = self._outpost.heliports_parcel.heliports

        for p in heliports:
            if grid.get_cell_from_cartesian(p) == cell:
                return True

        return False
