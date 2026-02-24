from typing import Optional

from skyweaver.core.operations.operational_unit import OperationalUnit

from skyweaver.units.domain.frame.crs_projection_policies import (
    AEQDProjectionPolicy,
)
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.domain.parameters.domain_parameters import DomainParameters
from skyweaver.units.domain.frame.domain_builder import DomainBuilder
from skyweaver.units.domain.logistics.domain_outpost import DomainOutpost


class DomainUnit(OperationalUnit[DomainOutpost]):

    BOUNDARY_OFFSET_IN_METERS = 1000.0

    def __init__(self, outpost: Optional[DomainOutpost] = None):
        super().__init__(outpost or DomainOutpost())

    def run(self) -> None:

        geodata = self._outpost.geodata

        # 1️⃣ Collect layers
        layers = []

        if not geodata.heliports.empty:
            layers.append(geodata.heliports)

        if not geodata.vertiports.empty:
            layers.append(geodata.vertiports)

        if not layers:
            raise ValueError("DomainUnit requires at least one spatial layer.")

        print(f"Collected {len(layers)} layers for domain construction.")
        parameters = DomainParameters.from_yaml_parcel(self._outpost.yaml_parcel)
        builder = DomainBuilder(projection_policy=AEQDProjectionPolicy())

        domain = builder.build(
            layers=layers,
            padding=parameters.padding,
            margin=parameters.margin,
        )

        # 4️⃣ Publish
        with self._outpost:
            self._outpost.domain_parcel = DomainParcel(domain)
