from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.geodata_domain_alignment.logistics.alignment_outpost import (
    GDProjectionOutpost,
)


class AlignmentUnit(OperationalUnit[GDProjectionOutpost]):
    """
    A AlignmentUnit is a specialized OperationalUnit that focuses on geodata domain alignment operations and logic.
    It serves as a foundational building block for units that require geodata domain alignment functionality,
    such as handling geodata-specific data, implementing geodata-specific algorithms, or managing
    geodata-specific interactions within the system.
    """

    def __init__(self, outpost: Optional[GDProjectionOutpost] = None):
        if outpost is None:
            outpost = GDProjectionOutpost()

        super().__init__(outpost)

    def run(self):

        raw_geodata = self._outpost.geodata
        domain = self._outpost.domain.domain

        if domain is None:
            raise ValueError("AlignmentUnit requires a valid Domain instance.")

        # ---- Heliports ----
        aligned_heliports = domain.to_local(raw_geodata.heliports)
        aligned_vertiports = domain.to_local(raw_geodata.vertiports)

        # Publish aligned data
        with self._outpost:
            self._outpost.heliports_parcel.heliports = aligned_heliports
            self._outpost.vertiports_parcel.vertiports = aligned_vertiports
