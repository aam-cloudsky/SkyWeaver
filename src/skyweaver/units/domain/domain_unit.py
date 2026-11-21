from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.model.sites import SourceGeoData
from skyweaver.units.domain.domain_construction import build_domain
from skyweaver.units.domain.logistics.domain_outpost import DomainOutpost
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.yaml_loader.parcel_conversion import configuration_of


class DomainUnit(OperationalUnit[DomainOutpost]):

    BOUNDARY_OFFSET_IN_METERS = 1000.0

    def __init__(self, outpost: Optional[DomainOutpost] = None):
        super().__init__(outpost or DomainOutpost())

    def run(self) -> None:

        geodata = self._outpost.geodata
        domain = build_domain(
            SourceGeoData(heliports=geodata.heliports, vertiports=geodata.vertiports),
            configuration_of(self._outpost.yaml_parcel),
        )

        with self._outpost:
            self._outpost.domain_parcel = DomainParcel(domain)
