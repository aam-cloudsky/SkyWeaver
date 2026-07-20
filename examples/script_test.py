from dataclasses import dataclass, field
from typing import Optional
from skyweaver.core.logistics.parcel.parcel import Parcel
from skyweaver.core.logistics.depot import Depot
from skyweaver.core.logistics.endpoint.outpost import Outpost, ParcelRole


# -------------------------------------------------
# Dummy Parcel
# -------------------------------------------------
@dataclass
class FuelParcel(Parcel):
    amount: Optional[float] = 0.0
    other: Optional[float] = 0.0


@dataclass
class OtherParcel(Parcel):
    is_true: bool = True


# -------------------------------------------------
# Dummy Outpost
# -------------------------------------------------


@dataclass
class ExampleOutpost(Outpost):
    fuel: FuelParcel = field(
        default_factory=FuelParcel, metadata={"role": ParcelRole.PRODUCED}
    )
    other: OtherParcel = field(
        default_factory=OtherParcel, metadata={"role": ParcelRole.PRODUCED}
    )


# -------------------------------------------------
# Test
# -------------------------------------------------
def main():

    depot = Depot()

    print("Creating outposts...")
    a = ExampleOutpost()
    b = ExampleOutpost()

    print("Initial state:")
    print("A:", a.fuel.amount)
    print("B:", b.fuel.amount)

    print("\nUpdating A...")
    with a:
        a.fuel = FuelParcel(amount=100.0)

    print("\nAfter update:")
    print("A:", a.fuel.amount, a.fuel.other)
    print("B:", b.fuel.amount, b.fuel.other)

    c = ExampleOutpost()

    print("\nAfter A update and creating C:")
    print("A:", a.fuel.amount, a.fuel.other)
    print("B:", b.fuel.amount, b.fuel.other)
    print("C:", c.fuel.amount, c.fuel.other)

    with b:
        fuel = b.fuel
        fuel.other = 50.0

    print("\nAfter update 2:")
    print("A:", a.fuel.amount, a.fuel.other)
    print("B:", b.fuel.amount, b.fuel.other)
    print("C:", c.fuel.amount, c.fuel.other)


if __name__ == "__main__":
    main()
