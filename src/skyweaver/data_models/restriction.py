from dataclasses import dataclass

import numpy as np
from shapely import Point
from skyweaver.enums.shapes import RestrictionShape
from skyweaver.enums.restriction_source import RestrictionSource



@dataclass
class Restriction:
    id: int
    shape: RestrictionShape
    radius: int  # in meters
    source: RestrictionSource
    location: Point = Point(0.0, 0.0)
    rotation: float = 0.0  # in radians, clockwise. -pi to pi

    def __repr__(self):
        return f"Restriction(id={self.id}, location={self.location}, shape={self.shape}, radius={self.radius}, rotation={self.rotation}, source={self.source})"

    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "shape": self.shape.name,
            "radius": self.radius,
            "rotation": self.rotation,
            "source": self.source.name,
        }

    @property
    def geometry_signature(self) -> tuple:
        """
        Returns a hashable signature that identifies the cacheable geometry.
        - Rotation is converted to degrees and rounded.
        - Location is excluded (does not affect the base geometry).
        """
        degree = round(np.degrees(self.rotation))  # default quantization = 1 degree
        return (self.shape, self.radius, degree)

if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt
    from skyweaver.enums.shapes import RestrictionShape
    from skyweaver.enums.restriction_source import RestrictionSource
    from skyweaver.data_models.restriction import Restriction
    from skyweaver.managers.components.stamp import Stamp

    # 1. Create restrictions
    disk = Restriction(
        id=1,
        shape=RestrictionShape.DISK,
        radius=10000,
        source=RestrictionSource.UNKNOWN,
        rotation=0.0,
    )

    sector0 = Restriction(
        id=2,
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=10000,
        source=RestrictionSource.UNKNOWN,
        rotation=0,
    )

    sector45 = Restriction(
        id=3,
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=10000,
        source=RestrictionSource.UNKNOWN,
        rotation=np.pi / 4,  # 45 degrees
    )

    # 2. Generate masks
    cell_size = 10  # in meters (fractions don't make sense at km scale)
    mask_disk = Stamp.to_cell_mask(disk, cell_size)
    mask_sector0 = Stamp.to_cell_mask(sector0, cell_size)
    mask_sector45 = Stamp.to_cell_mask(sector45, cell_size)

    # 3. Plot masks
    def plot_mask(mask, title: str):
        plt.imshow(mask, cmap="Greys", origin="lower")
        plt.title(title)
        plt.show()

    print("Plotting DISK:")
    plot_mask(mask_disk, "Disk")

    print("Plotting Circular Sector 0°:")
    plot_mask(mask_sector0, "Circular Sector 0°")

    print("Plotting Circular Sector 45°:")
    plot_mask(mask_sector45, "Circular Sector 45°")

