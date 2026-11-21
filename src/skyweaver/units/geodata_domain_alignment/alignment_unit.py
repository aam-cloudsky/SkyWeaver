from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.model.sites import SourceGeoData
from skyweaver.units.geodata_domain_alignment.alignment import (
    align_heliports,
    align_vertiports,
)
from skyweaver.units.geodata_domain_alignment.logistics.alignment_outpost import (
    GDProjectionOutpost,
)


class AlignmentUnit(OperationalUnit[GDProjectionOutpost]):
    """Expresses the heliports and vertiports in the local frame of the domain."""

    def __init__(self, outpost: Optional[GDProjectionOutpost] = None):
        if outpost is None:
            outpost = GDProjectionOutpost()

        super().__init__(outpost)

    def run(self):

        raw_geodata = self._outpost.geodata
        domain = self._outpost.domain.domain

        if domain is None:
            raise ValueError("AlignmentUnit requires a valid Domain instance.")

        geodata = SourceGeoData(
            heliports=raw_geodata.heliports, vertiports=raw_geodata.vertiports
        )

        with self._outpost:
            self._outpost.heliports_parcel.heliports = list(
                align_heliports(geodata, domain).points
            )
            self._outpost.vertiports_parcel.vertiports = list(
                align_vertiports(geodata, domain).points
            )
