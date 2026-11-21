"""Express the source data in the local frame of the domain."""

from __future__ import annotations

from skyweaver.model.sites import CandidateVertiports, Heliports, SourceGeoData
from skyweaver.units.domain.frame.domain import Domain


def align_heliports(geodata: SourceGeoData, domain: Domain) -> Heliports:
    return Heliports(points=tuple(domain.to_local(geodata.heliports)))


def align_vertiports(geodata: SourceGeoData, domain: Domain) -> CandidateVertiports:
    return CandidateVertiports(points=tuple(domain.to_local(geodata.vertiports)))
