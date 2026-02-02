from dataclasses import dataclass, field
from typing import Optional

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.core.logistics.depot import Depot
from skyweaver.core.logistics.outpost import Outpost, ParcelRole


# -------------------------------------------------
# Parcels
# -------------------------------------------------

@dataclass
class FuelParcel(Parcel):
    amount: Optional[float] = 0.0
    other: Optional[float] = 0.0


@dataclass
class KmParcel(Parcel):
    km: float = 0.0


@dataclass
class KmPerGallon(Parcel):
    km_per_gallon: float = 0.0



# -------------------------------------------------
# Outposts
# -------------------------------------------------

@dataclass
class GasStationOutpost(Outpost):
    fuel: FuelParcel = field(
        default_factory=FuelParcel,
        metadata={"role": ParcelRole.PRODUCED}
    )


@dataclass
class FuelOutpost(Outpost):
    fuel: FuelParcel = field(
        default_factory=FuelParcel,
        metadata={"role": ParcelRole.CONSUMED}
    )


@dataclass
class OdometerOutpost(Outpost):
    km: KmParcel = field(
        default_factory=KmParcel,
        metadata={"role": ParcelRole.PRODUCED}
    )


@dataclass
class CarOutpost(Outpost):
    fuel: FuelParcel = field(
        default_factory=FuelParcel,
        metadata={"role": ParcelRole.MUTATES}
    )

    km: KmParcel = field(
        default_factory=KmParcel,
        metadata={"role": ParcelRole.MUTATES}
    )


@dataclass
class GasConsumptionOutpost(Outpost):

    fuel: FuelParcel = field(
        default_factory=FuelParcel,
        metadata={"role": ParcelRole.CONSUMED}
    )

    km: KmParcel = field(
        default_factory=KmParcel,
        metadata={"role": ParcelRole.CONSUMED}
    )

    km_per_gallon: KmPerGallon = field(
        default_factory=KmPerGallon,
        metadata={"role": ParcelRole.PRODUCED}
    )



# -------------------------------------------------
# Test
# -------------------------------------------------

# -------------------------------------------------
# Test
# -------------------------------------------------

def main():

    depot = Depot()

    print("Creating outposts...")
    gas = GasStationOutpost()
    fuel_view = FuelOutpost()
    odometer = OdometerOutpost()
    car = CarOutpost()

    print("\nInitial state (everything invalid):")
    print("Gas fuel:", gas.fuel.amount)
    print("Fuel view:", fuel_view.fuel.amount)
    print("Odometer km:", odometer.km.km)

    # -------------------------------------------------
    # 1) PRODUCE fuel → VALID
    # -------------------------------------------------
    print("\nProducing fuel at gas station...")
    with gas:
        gas.fuel = FuelParcel(amount=100.0)

    # -------------------------------------------------
    # 2) PRODUCE km → VALID
    # -------------------------------------------------
    print("\nProducing km via odometer...")
    with odometer:
        odometer.km = KmParcel(km=200.0)

    print("\nAfter initial production:")
    print("Fuel:", fuel_view.fuel.amount)
    print("Km:", odometer.km.km)

    # -------------------------------------------------
    # 3) PRODUCE derived metric → INVALIDATION
    # -------------------------------------------------
    consumption = GasConsumptionOutpost()

    print("\nProducing km_per_gallon...")
    with consumption:
        consumption.km_per_gallon = KmPerGallon(
            km_per_gallon=(odometer.km.km or 0) / (gas.fuel.amount or 1)
        )

    print("\nMutating fuel and km (should INVALIDATE km_per_gallon)...")
    with car:
        car.fuel = FuelParcel(amount=(fuel_view.fuel.amount or 0) - 10.0)
        car.km = KmParcel(km=(odometer.km.km or 0) + 50.0)


if __name__ == "__main__":
    main()
