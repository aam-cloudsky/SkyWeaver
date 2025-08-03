import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from shapely import Point, Polygon
from shapely.affinity import rotate
from skyweaver.enums.shapes import RestrictionShape
from skyweaver.enums.restriction_source import RestrictionSource


@dataclass
class Restriction:
    id: int
    shape: RestrictionShape
    radius: float  # in meters
    source: RestrictionSource
    location: Point = Point(0.0, 0.0)
    rotation: float = 0.0  # in radians, clockwise

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

    def _retrieve_polygon(self) -> Polygon:
        """
        Returns the polygon representation of the restriction shape.
        """
        if self.shape == RestrictionShape.DISK:
            return self._disk_polygon()
        elif self.shape == RestrictionShape.RECTANGLE:
            return self._rectangle_polygon()
        elif self.shape == RestrictionShape.CIRCULAR_SECTOR:
            return self._circular_sector_polygon()
        else:
            raise ValueError(f"Unsupported shape: {self.shape.name}")

    def to_polygon(self) -> Polygon:
  
        """
        Returns a local shapely Polygon centered at (0,0), representing the restriction's shape,
        already rotated by `self.rotation`. This acts like a 'stamp' that can be translated over a global grid.
        """

        polygon = self._retrieve_polygon()
        return rotate(polygon, angle=self.rotation, origin=Point(0, 0), use_radians=True)

    def _disk_polygon(self) -> Polygon:
        """
        Returns a circular polygon with the specified radius.
        """
        return Point(0, 0).buffer(self.radius, resolution=32)

    def _rectangle_polygon(self) -> Polygon:
        # radius is diagonal length, so half side is radius / sqrt(2)
        half_side = self.radius / np.sqrt(2)
        return Polygon([
            (- half_side, - half_side),
            (+ half_side, - half_side),
            (+ half_side, + half_side),
            (- half_side, + half_side),
        ])

    def _circular_sector_polygon(self, angle_rad: float = (2/3)*np.pi, n_points: int = 32) -> Polygon:
        #TODO: Can I remove this N_points parameter?
        """
        Returns a circular sector polygon with the specified angle in radians.
        The sector is centered at (0, 0) and extends out to the specified radius
        with the specified number of points.
        """
        start_angle = -angle_rad / 2
        end_angle = angle_rad / 2
        points: List[Point] = [Point(0, 0)]
        for i in range(n_points + 1):
            theta = start_angle + i * (end_angle - start_angle) / n_points
            x = + self.radius * np.cos(theta)
            y = + self.radius * np.sin(theta)
            points.append(Point(x, y))
        return Polygon(points)

    def to_cell_mask(self, cell_size: float) -> np.ndarray:
        """
        Converts this restriction (represented as a polygon) into a binary mask array.
        The output is a 2D grid (numpy array), where each cell represents a square of `cell_size` meters.
        A value of 1 means the cell intersects with the restriction area (polygon), 0 means it does not.
        The restriction polygon is centered at (0, 0), and this mask acts like a "stamp".

        Parameters:
            cell_size (float): Size of each cell in meters (e.g., 1.0 means 1m x 1m resolution)

        Returns:
            np.ndarray: Binary array mask indicating which cells intersect the polygon.
        """

        # Ensure bounding box covers entire rotated shape
        bounding_radius = self.radius * np.sqrt(2)

        # Convert meters to number of cells
        half_side_cells = int(np.ceil(bounding_radius / cell_size)) + 1
        grid_size = 2 * half_side_cells
        n_rows, n_cols = grid_size, grid_size

        # Coordinates of bottom-left corner of the grid
        min_x = -half_side_cells * cell_size
        min_y = -half_side_cells * cell_size

        # Initialize empty binary mask
        mask = np.zeros((n_rows, n_cols), dtype=np.int32)

        # Generate the base polygon (e.g., disk, square, sector)
        rotated_polygon = self.to_polygon()

        # Loop through the grid and test for intersection with the rotated polygon
        for i in range(n_rows):
            for j in range(n_cols):
                # Bottom-left corner of the current cell
                x0 = min_x + j * cell_size
                y0 = min_y + i * cell_size

                # Define the square polygon representing the cell
                cell = Polygon([
                    (x0, y0),
                    (x0 + cell_size, y0),
                    (x0 + cell_size, y0 + cell_size),
                    (x0, y0 + cell_size),
                ])

                # Set cell to 1 if intersects rotated polygon
                if cell.intersects(rotated_polygon):
                    mask[i, j] = 1

        return mask

    def plot_mask(self, mask: np.ndarray):
        plt.imshow(mask, cmap='Greys', origin='lower')
        plt.title("Restriction Mask")
        plt.show()


        #print("Imagem salva como restriction_mask.png")


if __name__ == "__main__":
    from skyweaver.enums.shapes import RestrictionShape
    from skyweaver.enums.restriction_source import RestrictionSource

    # 1. Criar duas restrições
    disk = Restriction(
        id=1,
        shape=RestrictionShape.DISK,
        radius=10.0,
        source=RestrictionSource.UNKNOWN,
        rotation=0.0
    )

    rectangle1 = Restriction(
        id=2,
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=10.0,
        source=RestrictionSource.UNKNOWN,
        rotation=0
    )

    rectangle2 = Restriction(
        id=2,
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=10.0,
        source=RestrictionSource.UNKNOWN,
        rotation=np.pi / 4  # 45 graus
    )

    # 2. Gerar máscaras
    cell_size = 0.1
    mask_disk = disk.to_cell_mask(cell_size)
    mask_rect = rectangle1.to_cell_mask(cell_size)
    mask_rect2 = rectangle2.to_cell_mask(cell_size)

    # 3. Plotar
    print("Plotando DISCO:")
    disk.plot_mask(mask_disk)

    print("Plotando Seção Circular 0 graus:")
    rectangle1.plot_mask(mask_rect)

    print("Plotando Seção Circular 45 graus:")
    rectangle2.plot_mask(mask_rect2)