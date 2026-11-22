"""Build the operational domain around the source data."""

from __future__ import annotations

from skyweaver.model.configuration import Configuration
from skyweaver.model.sites import SourceGeoData
from skyweaver.units.domain.frame.crs_projection_policies import AEQDProjectionPolicy
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.domain.frame.domain_builder import DomainBuilder
from skyweaver.units.domain.parameters.domain_parameters import DomainParameters


def build_domain(geodata: SourceGeoData, configuration: Configuration) -> Domain:
    """The domain that holds every non-empty layer, padded as configured."""

    layers = [
        layer for layer in (geodata.heliports, geodata.vertiports) if not layer.empty
    ]
    if not layers:
        raise ValueError("build_domain requires at least one spatial layer.")

    print(f"Collected {len(layers)} layers for domain construction.")
    parameters = DomainParameters.from_configuration(configuration)
    builder = DomainBuilder(projection_policy=AEQDProjectionPolicy())
    return builder.build(
        layers=layers,
        padding=parameters.padding,
        margin=parameters.margin,
    )
