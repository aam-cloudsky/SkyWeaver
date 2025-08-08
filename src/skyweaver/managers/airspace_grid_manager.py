# src/skyweaver/managers/airspace_grid.py

import geopandas as gpd
import numpy as np
from shapely import unary_union
from shapely.geometry import Polygon, Point
from typing import Tuple, Optional, Dict
from skyweaver.dataclasses.restriction import Restriction
from skyweaver.enums.grid_channels import GridChannels
from pyproj import Transformer
from math import atan2, cos, sin

from skyweaver.enums.restriction_source import RestrictionSource
from skyweaver.enums.shapes import RestrictionShape


class AirspaceGrid:
    """
    AirspaceGrid generates a spatial grid (channels-first np.ndarray) over a given map.
    """

    def __init__(
        self,
        source_map: gpd.GeoDataFrame,
        cell_size: float = 500.0,  # metros por célula
        grid_crs: str = "EPSG:31983",  # ver nota sobre CRS abaixo
    ):
        """
        Initializes the airspace grid.

        Args:
            source_map: GeoDataFrame representing the region (qualquer CRS).
            cell_size: Size of each cell in meters.
            grid_crs: Projected CRS em metros (ex.: UTM).
        """
        self.crs: str = grid_crs
        self.source_map: gpd.GeoDataFrame = source_map.to_crs(self.crs)
        self.cell_size = cell_size
        #self.grid = self._create_grid(cell_size=self.cell_size)

        self.init_grid()

        # canalização channels-first
        #self._init_layers()

        # agora dicionário por id
        self.restrictions: Dict[int, Restriction] = {}
        self._restriction_counter = 0

        # pivô para ângulo (centroide do mapa no CRS do grid)
        self._pivot: Point = self.source_map.unary_union.centroid

        # transformer 4326->grid (para pontos em lat/lon)
        self._t_4326_to_grid = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)

    # ======== Restriction bookkeeping ========

    def _next_id(self) -> int:
        current = self._restriction_counter
        self._restriction_counter += 1
        return current

    def _to_grid_crs(self, point: Point, from_epsg: Optional[str] = None) -> Point:
        """
        Converte um Point para o CRS do grid. Se from_epsg=None, assume já estar no CRS do grid.
        """
        if from_epsg is None or from_epsg == self.crs:
            return point
        if from_epsg == "EPSG:4326":
            x, y = self._t_4326_to_grid.transform(point.x, point.y)
            return Point(x, y)
        # fallback genérico
        transformer = Transformer.from_crs(from_epsg, self.crs, always_xy=True)
        x, y = transformer.transform(point.x, point.y)
        return Point(x, y)

    def add_restriction(
        self,
        shape: RestrictionShape,
        radius: float,
        location: Point,
        source: RestrictionSource = RestrictionSource.UNKNOWN,
        rotation: float = 0.0,
        location_epsg: Optional[str] = "EPSG:4326",
    ) -> int:
        """
        Adds a restriction polygon to the grid.

        location: Point possivelmente em EPSG:4326 (lon, lat). Use location_epsg para declarar.
        """
        loc_grid = self._to_grid_crs(location, from_epsg=location_epsg)
        rid = self._next_id()
        restriction = Restriction(
            id=rid,
            shape=shape,
            radius=radius,
            source=source,
            location=loc_grid,
            rotation=rotation,
        )
        self.restrictions[rid] = restriction
        return rid

    def remove_restriction(self, restriction_id: int) -> bool:
        return self.restrictions.pop(restriction_id, None) is not None

    # ======== Grid generation / layers ========

    def _create_grid(self, cell_size: float) -> np.ndarray:
        minx, miny, maxx, maxy = self.source_map.total_bounds
        width = maxx - minx
        height = maxy - miny

        n_cols = int(np.ceil(width / cell_size))
        n_rows = int(np.ceil(height / cell_size))

        grid = np.zeros((len(GridChannels), n_rows, n_cols), dtype=bool)

        polygons = []
        for i in range(n_rows):
            for j in range(n_cols):
                x0 = minx + j * cell_size
                y0 = miny + i * cell_size
                poly = Polygon(
                    [
                        (x0, y0),
                        (x0 + cell_size, y0),
                        (x0 + cell_size, y0 + cell_size),
                        (x0, y0 + cell_size),
                    ]
                )
                polygons.append(poly)

        cells_gdf = gpd.GeoDataFrame(geometry=polygons, crs=self.crs)
        mask = cells_gdf.intersects(unary_union(self.source_map.geometry))
        grid[GridChannels.CITY_MASK.value] = (
            mask.to_numpy().reshape((n_rows, n_cols)).astype(bool)
        )
        return grid

    def init_grid(self):
        self.grid = self._create_grid(cell_size=self.cell_size)
        self._init_layers()

    def _init_layers(self):
        """
        Zera/certifica os canais extras (ex.: RESTRICTION).
        """
        if self.grid is None:
            return
        # Garante que o canal de restrição começa zerado
        self.grid[GridChannels.RESTRICTION.value, :, :] = False

    # ======== Apply restriction masks ========

    def apply_restrictions(self):
        """
        Applies all registered restriction masks to the grid.
        """
        if not self.restrictions:
            return

        for rid, restriction in self.restrictions.items():
            mask = restriction.to_cell_mask(self.cell_size)  # (h, w)
            h, w = mask.shape

            cell = self.point_to_cell(restriction.location)
            if cell is None:
                # fora da área — ignore ou logue
                continue

            row, col = cell
            top = row - h // 2
            left = col - w // 2
            channel = GridChannels.RESTRICTION.value

            # recorte dentro dos limites
            i0 = max(0, -top)
            j0 = max(0, -left)
            i1 = min(h, self.grid.shape[1] - top)
            j1 = min(w, self.grid.shape[2] - left)

            if i0 < i1 and j0 < j1:
                g_top = max(0, top)
                g_left = max(0, left)
                submask = mask[i0:i1, j0:j1]
                # aplica como OR
                self.grid[channel, g_top : g_top + submask.shape[0], g_left : g_left + submask.shape[1]] |= submask.astype(bool)


    # ======== Angular position API (sem expor Restriction) ========

    def _angle_of_point(self, p: Point) -> float:
        return atan2(p.y - self._pivot.y, p.x - self._pivot.x)

    def _radius_of_point(self, p: Point) -> float:
        return ((p.x - self._pivot.x) ** 2 + (p.y - self._pivot.y) ** 2) ** 0.5

    def get_restriction_angle(self, restriction_id: int) -> Optional[float]:
        r = self.restrictions.get(restriction_id)
        if r is None:
            return None
        return self._angle_of_point(r.location)

    def get_all_restriction_angles(self) -> Dict[int, float]:
        return {rid: self._angle_of_point(r.location) for rid, r in self.restrictions.items()}

    def set_restriction_angle(
        self,
        restriction_id: int,
        theta: float,
        *,
        keep_radius: bool = True,
        radius: Optional[float] = None,
    ) -> bool:
        """
        update retriction angular position.
        Se keep_radius=True, preserva o raio atual; senão, usa 'radius'.
        """
        r = self.restrictions.get(restriction_id)
        if r is None:
            return False

        if keep_radius:
            rad = self._radius_of_point(r.location)
        else:
            if radius is None:
                return False
            rad = radius

        newx = self._pivot.x + rad * cos(theta)
        newy = self._pivot.y + rad * sin(theta)
        r.location = Point(newx, newy)
        return True
    
    def rotate_restrictions(self, radians: Dict[int, float]):
        """
        updates restriction angles based on restrinction ids. angle must be in radians"""
        for id, radian in radians.items():

            self.restrictions[id].rotation = radian


    def compute_free_space_pct(self) -> float:
        """
        Fraction of free airspace over the ENTIRE grid (for quick dashboards).
        Prefer absolute metrics (cells/area) for sensitivity analyses.
        """
        rest = self.grid[GridChannels.RESTRICTION.value]
        total_cells = rest.size
        if total_cells == 0:
            return 1.0
        restricted = np.count_nonzero(rest)
        return 1.0 - (restricted / total_cells)

    def get_cycle_metrics(self) -> Dict[str, float]:
        """
        Return a compact metrics dict for logging/telemetry.
        """
        rest = self.grid[GridChannels.RESTRICTION.value]
        total_cells = rest.size
        restricted_cells = int(np.count_nonzero(rest))
        free_pct = 1.0 - (restricted_cells / total_cells) if total_cells else 1.0
        return {
            "n_restrictions": float(len(self.restrictions)),
            "restricted_cells": float(restricted_cells),
            "restricted_area_m2": float(restricted_cells * (self.cell_size ** 2)),
            "total_cells": float(total_cells),
            "free_space_pct": float(free_pct),
        }

    
    # ======== Utils ========

    def to_geodataframe(self) -> Optional[gpd.GeoDataFrame]:
        # (Placeholder — você pode expandir para exportar geometrias das células)
        if self.grid is None:
            return None
        return gpd.GeoDataFrame(
            {
                "valid": self.grid[GridChannels.CITY_MASK.value].ravel(),
                "restricted": self.grid[GridChannels.RESTRICTION.value].ravel(),
            }
        )

    def point_to_cell(self, point: Point) -> Optional[Tuple[int, int]]:
        minx, miny, _, _ = self.source_map.total_bounds
        col = int((point.x - minx) // self.cell_size)
        row = int((point.y - miny) // self.cell_size)
        if 0 <= row < self.grid.shape[1] and 0 <= col < self.grid.shape[2]:
            return row, col
        return None

    def reset(self):
        """
        Reset retrition channel
        """
        self.grid[GridChannels.RESTRICTION.value, :, :] = False  # clear restriction layer



    def plot_graph(self):
  
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        axes[0].set_title("CITY_MASK")
        im0 = axes[0].imshow(mgr.grid[GridChannels.CITY_MASK.value], origin="lower")
        fig.colorbar(im0, ax=axes[0], fraction=0.046)

        axes[1].set_title("RESTRICTION")
        im1 = axes[1].imshow(mgr.grid[GridChannels.RESTRICTION.value], origin="lower")
        fig.colorbar(im1, ax=axes[1], fraction=0.046)

        for ax in axes:
            ax.set_xlabel("col")
            ax.set_ylabel("row")
        plt.tight_layout()
        plt.show()

    def compute_restricted_cells(self) -> int:
        """
        Return the absolute number of restricted cells over the entire grid.
        """
        rest = self.grid[GridChannels.RESTRICTION.value]
        return int(np.count_nonzero(rest))

    def compute_restricted_area_m2(self) -> float:
        """
        Return the restricted area in square meters, i.e., restricted_cells * (cell_size^2).
        """
        return float(self.compute_restricted_cells() * (self.cell_size ** 2))


        
if __name__ == "__main__":
    """
    Teste local rápido:
    - Cria um mapa retangular sintético
    - Gera grid
    - Adiciona 3 restrições circulares (raio em metros)
    - Aplica e plota CITY_MASK e RESTRICTION
    """
    import matplotlib.pyplot as plt

    # 1) mapa retangular simples no CRS do grid (por ex. UTM 23S, metros)
    #    Aqui: um retângulo 10km x 8km
    grid_crs = "EPSG:31983"
    rect = Polygon([(0, 0), (10_000, 0), (10_000, 8_000), (0, 8_000)])
    gdf = gpd.GeoDataFrame(geometry=[rect], crs=grid_crs)

    mgr = AirspaceGrid(gdf, cell_size=20.0, grid_crs=grid_crs)

    # 2) adiciona restrições – duas no CRS do grid e uma em lat/lon (exemplo fictício)
    #    (se você tiver lat/lon reais, troque location_epsg="EPSG:4326" e passe lon,lat)


    r1 = mgr.add_restriction(
        shape=RestrictionShape.DISK,
        radius=1200.0,
        location=Point(2500, 2500),
        source=RestrictionSource.HELIPORT,
        rotation=0.0,
        location_epsg=grid_crs,
    )
    r2 = mgr.add_restriction(
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=800.0,
        location=Point(7500, 3000),
        source=RestrictionSource.HELIPORT,
        location_epsg=grid_crs,
    )
    r3 = mgr.add_restriction(
        shape=RestrictionShape.CIRCULAR_SECTOR, #square not working
        radius=1000.0,
        location=Point(8000, 3000),
        source=RestrictionSource.UNKNOWN,
        location_epsg=grid_crs,
        rotation=np.pi
    )


    mgr.reset()
    mgr.rotate_restrictions({r1:np.pi, r2:1.0, r3:np.pi + 0.5})
    mgr.apply_restrictions()
    mgr.plot_graph()


    m = mgr.get_cycle_metrics()
    print(f"[metrics] restricted_cells={int(m['restricted_cells'])} "
        f"restricted_area_m2={m['restricted_area_m2']:.2f} free_space_pct={m['free_space_pct']:.6f}")

    mgr.reset()
    mgr.rotate_restrictions({r1:0.0, r2:3.0, r3:np.pi})
    mgr.apply_restrictions()
    mgr.plot_graph()

    # Example: log absolute metrics to enable before/after comparisons outside this class
    m = mgr.get_cycle_metrics()
    print(f"[metrics] restricted_cells={int(m['restricted_cells'])} "
        f"restricted_area_m2={m['restricted_area_m2']:.2f} free_space_pct={m['free_space_pct']:.6f}")


    
    
