from dataclasses import dataclass, field
from typing import Optional

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.core.logistics.depot import Depot
from skyweaver.core.logistics.outpost import Outpost, ParcelRole


# -------------------------------------------------
# Parcels
# -------------------------------------------------


@dataclass
class FuelLevel(Parcel):
    liters: float = 0.0


@dataclass
class DistanceTraveled(Parcel):
    km: float = 0.0


@dataclass
class FuelEfficiency(Parcel):
    km_per_liter: float = 0.0



# -------------------------------------------------
# Outposts
# -------------------------------------------------

@dataclass
class VehicleStateOutpost(Outpost):
    fuel: FuelLevel = field(
        default_factory=FuelLevel,
        metadata={"role": ParcelRole.MUTATES}
    )

    distance: DistanceTraveled = field(
        default_factory=DistanceTraveled,
        metadata={"role": ParcelRole.MUTATES}
    )


@dataclass
class FuelSensorOutpost(Outpost):
    fuel: FuelLevel = field(
        default_factory=FuelLevel,
        metadata={"role": ParcelRole.PRODUCED}
    )


@dataclass
class OdometerSensorOutpost(Outpost):
    distance: DistanceTraveled = field(
        default_factory=DistanceTraveled,
        metadata={"role": ParcelRole.PRODUCED}
    )


@dataclass
class EfficiencyCalculatorOutpost(Outpost):
    fuel: FuelLevel = field(
        default_factory=FuelLevel,
        metadata={"role": ParcelRole.CONSUMED}
    )

    distance: DistanceTraveled = field(
        default_factory=DistanceTraveled,
        metadata={"role": ParcelRole.CONSUMED}
    )

    efficiency: FuelEfficiency = field(
        default_factory=FuelEfficiency,
        metadata={"role": ParcelRole.PRODUCED}
    )



# -------------------------------------------------
# Test
# -------------------------------------------------

def print_state(vehicle, fuel_sensor, odometer, efficiency):
    print(
        f"[VehicleState]   fuel={vehicle.fuel.liters:6.1f} L | "
        f"distance={vehicle.distance.km:6.1f} km"
    )
    print(f"[FuelSensor]    fuel={fuel_sensor.fuel.liters:6.1f} L")
    print(f"[Odometer]      distance={odometer.distance.km:6.1f} km")
    print(
        f"[Efficiency]    km_per_liter={efficiency.efficiency.km_per_liter:6.2f}")
    print()


def main():
    depot = Depot()

    print("Creating outposts...")
    vehicle = VehicleStateOutpost()
    fuel_sensor = FuelSensorOutpost()
    odometer = OdometerSensorOutpost()
    efficiency = EfficiencyCalculatorOutpost()

    # -------------------------------------------------
    # Initial shared state
    # -------------------------------------------------
    print("\n--- Initial shared state (no valid derived data) ---")
    print_state(vehicle, fuel_sensor, odometer, efficiency)

    # -------------------------------------------------
    # Fuel sensor updates shared state
    # -------------------------------------------------
    print("Fuel sensor reports refueling event (shared state changes)")
    with fuel_sensor:
        fuel_sensor.fuel = FuelLevel(liters=60.0)

    print_state(vehicle, fuel_sensor, odometer, efficiency)

    # -------------------------------------------------
    # Odometer sensor updates shared state
    # -------------------------------------------------
    print("Odometer sensor reports vehicle movement (shared state changes)")
    with odometer:
        odometer.distance = DistanceTraveled(km=30.0)

    print_state(vehicle, fuel_sensor, odometer, efficiency)

    # -------------------------------------------------
    # Compute derived metric (becomes VALID)
    # -------------------------------------------------
    print("Computing fuel efficiency from valid shared state")
    with efficiency:
        efficiency.efficiency = FuelEfficiency(
            km_per_liter=(
                odometer.distance.km / fuel_sensor.fuel.liters
                if fuel_sensor.fuel.liters > 0 else 0
            )
        )

    print_state(vehicle, fuel_sensor, odometer, efficiency)

    # -------------------------------------------------
    # Vehicle mutates shared state (INVALIDATES derived)
    # -------------------------------------------------
    print("Vehicle state mutates (invalidates derived efficiency)")
    with vehicle:
        vehicle.fuel = FuelLevel(liters=40.0)
        vehicle.distance = DistanceTraveled(km=120.0)

    print_state(vehicle, fuel_sensor, odometer, efficiency)

    # -------------------------------------------------
    # Recompute derived metric
    # -------------------------------------------------
    print("Recomputing fuel efficiency after state mutation")
    with efficiency:
        efficiency.efficiency = FuelEfficiency(
            km_per_liter=(
                odometer.distance.km / fuel_sensor.fuel.liters
                if fuel_sensor.fuel.liters > 0 else 0
            )
        )

    print_state(vehicle, fuel_sensor, odometer, efficiency)

    # -------------------------------------------------
    # Sensor update breaks validity again
    # -------------------------------------------------
    print("Fuel sensor reports refueling (derived efficiency becomes stale)")
    with fuel_sensor:
        fuel_sensor.fuel = FuelLevel(liters=60.0)

    print_state(vehicle, fuel_sensor, odometer, efficiency)


if __name__ == "__main__":
    main()


