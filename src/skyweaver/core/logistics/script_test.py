from dataclasses import dataclass, field
from skyweaver.core.logistics.parcel import Parcel
from skyweaver.core.logistics.depot import Depot
from skyweaver.core.logistics.outpost import Outpost


# -------------------------------------------------
# Dummy Parcel
# -------------------------------------------------
@dataclass
class FuelParcel(Parcel):
    amount: float = 0.0
    other: float = 0.1


# -------------------------------------------------
# Dummy Outpost
# -------------------------------------------------
@dataclass
class BaseOutpost(Outpost):
    fuel: FuelParcel = field(default_factory=FuelParcel)


# -------------------------------------------------
# Test
# -------------------------------------------------
def main():
    depot = Depot()

    print("Creating outposts...")
    a = BaseOutpost()
    b = BaseOutpost()

    print("Initial state:")
    print("A:", a.fuel.amount)
    print("B:", b.fuel.amount)

    print("\nUpdating A...")
    with a:
        a.fuel = FuelParcel(amount=100.0)

    print("\nAfter update:")
    print("A:", a.fuel.amount, a.fuel.other)
    print("B:", b.fuel.amount, b.fuel.other)

    c = BaseOutpost()

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
