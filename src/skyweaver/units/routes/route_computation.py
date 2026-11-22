"""The airspace graph and the routes between the vertiports."""

from __future__ import annotations

from skyweaver.model.cells import RestrictedCells
from skyweaver.model.configuration import Configuration
from skyweaver.model.routes import Routes
from skyweaver.model.sites import Vertiports
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.routes.connectivity.connectivity_builder import interconnect
from skyweaver.units.routes.graph.graph_builder import GraphBuilder
from skyweaver.units.routes.graph.graph_pack import AirspaceGraphPack
from skyweaver.units.routes.parameters.routing_parameters import RoutingParameters


def build_airspace_graph(grid: HexGrid, restricted: RestrictedCells) -> AirspaceGraphPack:
    """The graph of the domain cells that are not restricted."""

    return GraphBuilder.build_airspace_graph(grid, restricted.coords)


def compute_routes(
    airspace_graph: AirspaceGraphPack,
    vertiports: Vertiports,
    grid: HexGrid,
    configuration: Configuration,
) -> Routes:
    """Connect the vertiports through the airspace graph, as configured."""

    parameters = RoutingParameters.from_configuration(configuration)
    terminals = grid.get_cell_from_cartesians(vertiports.points)
    paths = interconnect(
        terminals=terminals,
        airspace_graph=airspace_graph,
        connectivity_mode=parameters.connectivity_mode,
        info={"k": parameters.k_neighbors},
    )
    return Routes(
        routes_graph=GraphBuilder.build_routes_graph(paths),
        terminals_graph=GraphBuilder.build_terminals_graph(paths),
    )
