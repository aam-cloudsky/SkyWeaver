from dataclasses import dataclass

from skyweaver.units.domain.domain_unit import DomainUnit
from skyweaver.units.geodata_domain_alignment.alignment_unit import AlignmentUnit
from skyweaver.units.hexgrid.hexgrid_unit import HexGridUnit
from skyweaver.units.restriction.restriction_unit import RestrictionUnit
from skyweaver.units.routes.routes_unit import RoutesUnit
from skyweaver.units.sources.sources_unit import SourcesUnit
from skyweaver.units.yaml_loader.yaml_loader_unit import YAMLLoaderUnit


class RuntimeUnits:

    def __init__(self, config_path: str):

        self.yaml = YAMLLoaderUnit(yaml_path=config_path)

        self.sources = SourcesUnit()

        self.domain = DomainUnit()

        self.alignment = AlignmentUnit()

        self.grid = HexGridUnit()

        self.restriction = RestrictionUnit()

        self.routes = RoutesUnit()
