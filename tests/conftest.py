"""Shared fixtures: the Rio de Janeiro case study, computed with the flow functions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from skyweaver.model import (
    BaseVertiports,
    CandidateVertiports,
    ConfigPath,
    Configuration,
    HeliportCells,
    Heliports,
    SourceGeoData,
)
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.domain.domain_construction import build_domain
from skyweaver.units.geodata_domain_alignment.alignment import (
    align_heliports,
    align_vertiports,
)
from skyweaver.units.hexgrid.grid_construction import build_grid
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.restriction.restrictions import locate_heliport_cells
from skyweaver.units.routes.vertiports import filter_candidate_vertiports
from skyweaver.units.sources.geodata import load_geodata
from skyweaver.units.yaml_loader.configuration import load_configuration

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "examples" / "droneport_experiment" / "config.yaml"


@dataclass(frozen=True)
class CaseStudy:
    configuration: Configuration
    geodata: SourceGeoData
    domain: Domain
    heliports: Heliports
    candidates: CandidateVertiports
    heliport_cells: HeliportCells
    base: BaseVertiports

    def grid(self) -> HexGrid:
        """A fresh grid: tests that mark cells must not share one."""

        return build_grid(self.domain, self.configuration)


@pytest.fixture(scope="session")
def rio() -> CaseStudy:
    configuration = load_configuration(ConfigPath(CONFIG_PATH))
    geodata = load_geodata(configuration)
    domain = build_domain(geodata, configuration)
    grid = build_grid(domain, configuration)
    heliports = align_heliports(geodata, domain)
    candidates = align_vertiports(geodata, domain)
    heliport_cells = locate_heliport_cells(heliports, grid)
    base = filter_candidate_vertiports(candidates, heliport_cells, grid)
    return CaseStudy(
        configuration, geodata, domain, heliports, candidates, heliport_cells, base
    )


def xy(points) -> list[tuple[float, float]]:
    return [(point.x, point.y) for point in points]
