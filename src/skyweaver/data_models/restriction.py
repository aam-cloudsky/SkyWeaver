import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from shapely import Point, Polygon
from shapely.affinity import rotate
from skyweaver.enums.shapes import RestrictionShape
from skyweaver.enums.restriction_source import RestrictionSource
from skyweaver.managers.components.stamp import Stamp
from functools import cache

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

    @staticmethod
    @cache
    def _retrieve_polygon(shape: RestrictionShape, radius: int) -> Polygon:
        """
        Returns the polygon representation of the restriction shape.
        """
        if shape == RestrictionShape.DISK:
            return Restriction._disk_polygon(radius=radius)
        elif shape == RestrictionShape.RECTANGLE:
            return Restriction._rectangle_polygon(radius=radius)
        elif shape == RestrictionShape.CIRCULAR_SECTOR:
            return Restriction._circular_sector_polygon(radius=radius)
        else:
            raise ValueError(f"Unsupported shape: {shape.name}")

    """
    def to_polygon(self) -> Polygon:

        Returns a local shapely Polygon centered at (0,0), representing the restriction's shape,
        already rotated by `self.rotation`. This acts like a 'stamp' that can be translated over a global grid.


        polygon = self._retrieve_polygon(shape=self.shape, radius=self.radius)
        return rotate(
            polygon, angle=self.rotation, origin=Point(0, 0), use_radians=True
        )
    """

    @staticmethod
    @cache
    def _disk_polygon(radius: int) -> Polygon:
        """
        Returns a circular polygon with the specified radius.
        """
        return Point(0, 0).buffer(radius, resolution=32)

    @staticmethod
    @cache
    def _rectangle_polygon(radius: int) -> Polygon:
        # radius is diagonal length, so half side is radius / sqrt(2)
        half_side = radius / np.sqrt(2)
        return Polygon(
            [
                (-half_side, -half_side),
                (+half_side, -half_side),
                (+half_side, +half_side),
                (-half_side, +half_side),
            ]
        )

    @staticmethod
    @cache
    def _circular_sector_polygon(
        radius: int, angle_rad: float = (2 / 3) * np.pi
    ) -> Polygon:
        """
        Return a triangular polygon that approximates the circular sector.

        - Height: self.radius
        - Angle: angle_rad (default 120 degrees)
        """

        # ponto do vértice (no centro)
        apex = (0.0, 0.0)

        # ângulos para os dois cantos da base
        half_angle = angle_rad / 2.0

        # coordenadas dos vértices da base (distância = raio)
        p1 = (
            radius * np.cos(half_angle),
            radius * np.sin(half_angle),
        )
        p2 = (
            radius * np.cos(-half_angle),
            radius * np.sin(-half_angle),
        )

        # triângulo formado: ápice + dois pontos da base
        return Polygon([apex, p1, p2])

    """
    TODO: THIS POLYGON IS MORE PRECISE, BUT SLOWER. SHOULD I REMOVE IT?
    def _circular_sector_polygon(
        self, angle_rad: float = (2 / 3) * np.pi, n_points: int = 32
    ) -> Polygon:
        # TODO: Can I remove this N_points parameter?
        
        Returns a circular sector polygon with the specified angle in radians.
        The sector is centered at (0, 0) and extends out to the specified radius
        with the specified number of points.
        
        start_angle = -angle_rad / 2
        end_angle = angle_rad / 2
        points: List[Point] = [Point(0, 0)]
        for i in range(n_points + 1):
            theta = start_angle + i * (end_angle - start_angle) / n_points
            x = +self.radius * np.cos(theta)
            y = +self.radius * np.sin(theta)
            points.append(Point(x, y))
        return Polygon(points)
        """
    
    @staticmethod
    @cache
    # radius is in meters. It should be int to increase performance.
    # fraction of meters is too much for this problem.
    def _get_cached_stamp(shape: RestrictionShape, radius: int, cell_size: float) -> Stamp:
        base_polygon = Restriction._retrieve_polygon(shape, radius)
        return Stamp(base_polygon, cell_size)
    
    def to_cell_mask(self, cell_size: float) -> np.ndarray:
        # Recupera stamp cacheado
        stamp = self._get_cached_stamp(self.shape, self.radius, cell_size)
        # Aplica rotação dinâmica
        radian = self.rotation # -pi to pi
        step = 1
        degree = round(np.degrees(radian) / step) * step
        return stamp.rotated_mask(degree)
    
    """
    def to_cell_mask(self, cell_size: float) -> np.ndarray:
        
        Returns the rasterized mask of the restriction rotated by `self.rotation`.
        Uses IDEALStamp for fast repeated rotations.
        
        if not hasattr(self, "_ideal_stamp"):
            # Criar polígono base centrado em (0,0)
            base_polygon = self._retrieve_polygon()
            # Criar carimbo IDEAL
            self._ideal_stamp = Stamp(base_polygon, cell_size)
            # Guardar os bounds originais para alinhamento
            self._stamp_minx = self._ideal_stamp.minx
            self._stamp_miny = self._ideal_stamp.miny

        # Gerar máscara rotacionada usando ângulo atual
        mask_local = self._ideal_stamp.rotated_mask(self.rotation)

        return mask_local
    """

    def plot_mask(self, mask: np.ndarray):
        plt.imshow(mask, cmap="Greys", origin="lower")
        plt.title("Restriction Mask")
        plt.show()

        # print("Imagem salva como restriction_mask.png")


if __name__ == "__main__":
    from skyweaver.enums.shapes import RestrictionShape
    from skyweaver.enums.restriction_source import RestrictionSource

    # 1. Criar duas restrições
    disk = Restriction(
        id=1,
        shape=RestrictionShape.DISK,
        radius=10,
        source=RestrictionSource.UNKNOWN,
        rotation=0.0,
    )

    rectangle1 = Restriction(
        id=2,
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=10,
        source=RestrictionSource.UNKNOWN,
        rotation=0,
    )

    rectangle2 = Restriction(
        id=2,
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=10,
        source=RestrictionSource.UNKNOWN,
        rotation=np.pi / 4,  # 45 graus
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
