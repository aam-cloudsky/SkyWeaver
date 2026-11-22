"""Build the hexagonal grid over the operational bounds of the domain."""

from __future__ import annotations

from skyweaver.model.configuration import Configuration
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.hexgrid.parameters.grid_parameters import GridParameters
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid


def build_grid(domain: Domain, configuration: Configuration) -> HexGrid:
    parameters = GridParameters.from_configuration(configuration)
    return HexGrid(
        cell_size=parameters.cell_size,
        operational_bounds=domain.operational_bounds,
        orientation=parameters.orientation,
    )
