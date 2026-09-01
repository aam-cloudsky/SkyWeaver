from typing import List, Optional

from shapely.geometry import Point

from skyweaver.core.operations.operational_unit import OperationalUnit

from skyweaver.units.hexgrid.structure.hexcell import HexCell
from skyweaver.units.routes.graph.graph_builder import GraphBuilder
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost
from skyweaver.units.routes.routing import Routing
from skyweaver.units.routes.parameters.routing_parameters import RoutingParameters

from skyweaver.units.routes.connectivity.connectivity_builder import (
    interconnect,
)


class RoutesUnit(OperationalUnit[RoutesOutpost]):
    def __init__(self, outpost: Optional[RoutesOutpost] = None):

        if outpost is None:
            outpost = RoutesOutpost()
        super().__init__(outpost=outpost)

        print(
            "[RoutesUnit] TODO: Cluster Parcel Should be a Optional Consumed Parcel, therefore, 'CONSUMED' is not the right role"
        )
        self.builder = GraphBuilder(outpost=self._outpost)

        # NOTE: airspace_graph used to be built here, in __init__. That only
        # worked when RoutesUnit was constructed *after* HexGridUnit.run()
        # had already populated the grid (true for the legacy
        # DroneportExperimentApp, which constructs units interleaved with
        # run() calls). RuntimeUnits/ApplicationRuntime constructs every
        # unit up front, before any run() executes, so building the graph
        # here captured an empty/default grid (1 vertex, 0 edges) and left
        # routing permanently empty. Moved into run() below, which is
        # already re-invoked on every recomputation (see on_left_click in
        # the legacy app), so this is also the more correct home for it.

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
        # NOTE: previously compared `_from_cell_to_cartesian(cell)` (the
        # hex cell's center point) against the stored vertiport points
        # using exact Shapely Point equality. The stored points are the
        # original, continuous-space vertiport coordinates -- not snapped
        # to the cell center -- so this comparison almost never matched,
        # and RemoveVertiport silently no-op'd. Fixed to match the same
        # way add_vertiport/_is_cell_available do: by hex cell, not by
        # exact point.
        grid = self._outpost.grid_parcel.grid
        vertiports = self._outpost.vertiports_parcel.vertiports
        vertiport_cells = grid.get_cell_from_cartesians(vertiports)

        remaining = [
            vertiport
            for vertiport, vertiport_cell in zip(vertiports, vertiport_cells)
            if vertiport_cell != cell
        ]

        if len(remaining) == len(vertiports):
            return

        with self._outpost:
            self._outpost.vertiports_parcel.vertiports = remaining

    def clear_vertiports(self) -> None:
        with self._outpost:
            self._outpost.vertiports_parcel.vertiports.clear()

    def _get_vertiports(self) -> List[HexCell]:
        # combine local terminals with terminals from vertiports
        vertiports = self._outpost.vertiports_parcel.vertiports
        grid = self._outpost.grid_parcel.grid
        return grid.get_cell_from_cartesians(vertiports)

    def run(self) -> None:

        airspace_graph = self.builder.build_airspace_graph()

        with self._outpost:
            self._outpost.routes_parcel.airspace_graph = airspace_graph

        vertiports = self._get_vertiports()
        parameters = RoutingParameters.from_yaml_parcel(self._outpost.yaml_parcel)

        # paths: List[List[HexCell]] = Routing.compute_terminal_paths(
        #    airspace_graph,
        #    vertiports,
        #    connectivity_mode=parameters.connectivity_mode,
        #    k=parameters.k_neighbors,
        # )

        paths: List[List[HexCell]] = interconnect(
            terminals=vertiports,
            airspace_graph=airspace_graph,
            connectivity_mode=parameters.connectivity_mode,
            info={
                "k": parameters.k_neighbors,
            },
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
