# src/skyweaver/managers/airspace_grid.py

import time
import geopandas as gpd
import numpy as np
from shapely import unary_union
from shapely.geometry import Polygon, Point
from typing import Tuple, Optional, Dict
from skyweaver.data_models.restriction import Restriction
from skyweaver.enums.grid_channels import GridChannels
from pyproj import Transformer
from math import atan2, cos, sin

from skyweaver.enums.restriction_source import RestrictionSource
from skyweaver.enums.shapes import RestrictionShape
import matplotlib.pyplot as plt
from shapely.geometry import box
import geopandas as gpd

from skyweaver.managers.components.stamp import Stamp

import warnings
warnings.filterwarnings(
    "ignore",
    message="Starting a Matplotlib GUI outside of the main thread will likely fail",
    category=UserWarning
)



class AirspaceGrid:
    """
    AirspaceGrid generates a spatial grid (channels-first np.ndarray) over a given map.
    """

    def __init__(
        self,
        source_map: gpd.GeoDataFrame,
        cell_size: int = 500,  # metros por célula

    ):
        """
        Initializes the airspace grid.

        Args:
            source_map: GeoDataFrame representing the region (qualquer CRS).
            cell_size: Size of each cell in meters.
            grid_crs: Projected CRS em metros (ex.: UTM).
        """
        grid_crs: str = "EPSG:31983"  # ver nota sobre CRS abaixo
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
        #The getter for property "unary_union" is deprecated
        #Use method `union_all` instead
        #self._pivot: Point = self.source_map.union_all().centroid

        # transformer 4326->grid (para pontos em lat/lon)
        self._t_4326_to_grid = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)
    """
    def to_geodataframes(self) -> Dict[str, gpd.GeoDataFrame]:
        
        #Export each grid layer as a separate GeoDataFrame.
        #Returns a dict {layer_name: GeoDataFrame}.
        
        

        #crs = "EPSG:4326"  # WGS84 em graus
        minx, miny, maxx, maxy = self.source_map.total_bounds
        n_rows, n_cols = self.grid.shape[1], self.grid.shape[2]

        geodfs = {}

        for channel in GridChannels:
            mask = self.grid[channel.value]
            geometries = []
            values = []

            for i in range(n_rows):
                for j in range(n_cols):
                    if mask[i, j]:  # só exporta as células ativas
                        cell_minx = minx + j * self.cell_size
                        cell_miny = miny + i * self.cell_size
                        cell_maxx = cell_minx + self.cell_size
                        cell_maxy = cell_miny + self.cell_size
                        geometries.append(
                            box(cell_minx, cell_miny, cell_maxx, cell_maxy))
                        values.append(1)
            if len(geometries) == 0:
                continue

            geodfs[channel.name] = gpd.GeoDataFrame(
                geometry=geometries, crs=None)
        return geodfs
    """
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
        radius: int,
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

        return grid
    
    def get_restriction_mask(self) -> np.ndarray:
        return self.grid[GridChannels.RESTRICTION.value]

    def init_grid(self):
        self.grid: np.ndarray = self._create_grid(cell_size=self.cell_size)
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
            print("[DEBUG] No restrictions to apply.")
            return

        #print(f"[DEBUG] Applying {len(self.restrictions)} restrictions.")

        for rid, restriction in self.restrictions.items():
            #start_time = time.perf_counter()
            Stamp.to_cell_mask(restriction, self.cell_size)
            mask = Stamp.to_cell_mask(restriction, self.cell_size)  # (h, w)
            h, w = mask.shape

            # Debugging output
            # print(f"[DEBUG] Restriction {rid}: mask shape={mask.shape}")

            cell = self.point_to_cell(restriction.location)
            if cell is None:
                # fora da área — ignore ou logue
                continue

            row, col = cell
            top = row - h // 2
            left = col - w // 2
            channel = GridChannels.RESTRICTION.value

            #print(f"[DEBUG] Restriction {rid}: mask shape={mask.shape}, "
            #      f"grid pos=({row}, {col}), top={top}, left={left}")

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

    def get_restriction_rotation(self, restriction_id: int) -> Optional[float]:
        r = self.restrictions.get(restriction_id)
        if r is None:
            return None
        return r.rotation

    def get_all_restriction_rotations(self) -> Dict[int, float]:
        return {rid: r.rotation for rid, r in self.restrictions.items()}

    def set_restriction_rotation(
        self,
        restriction_id: int,
        theta: float,
    ) -> bool:
        """
        update retriction angular position.
        Se keep_radius=True, preserva o raio atual; senão, usa 'radius'.
        """
        r = self.restrictions.get(restriction_id)
        if r is None:
            return False


        r.rotation = theta
        return True
    
    def rotate_restrictions(self, id_radians: Dict[int, float]):
        """
        updates restriction angles based on restrinction ids. angle must be in radians"""

        for id, radian in id_radians.items():

            self.restrictions[id].rotation = radian

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

        for rid, _ in self.restrictions.items():
            self.rotate_restrictions({rid: 0.0})
            self.restrictions[rid].rotation = 0.0

    def clear_grid(self):
        """
        Clear only the restriction layer, keeping the current rotations.
        """
        self.grid[GridChannels.RESTRICTION.value, :, :] = False


    def plot_graph(self):
  
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        axes[0].set_title("CITY_MASK")
        im0 = axes[0].imshow(self.grid[GridChannels.CITY_MASK.value], origin="lower")
        fig.colorbar(im0, ax=axes[0], fraction=0.046)

        axes[1].set_title("RESTRICTION")
        im1 = axes[1].imshow(self.grid[GridChannels.RESTRICTION.value], origin="lower")
        fig.colorbar(im1, ax=axes[1], fraction=0.046)

        for ax in axes:
            ax.set_xlabel("col")
            ax.set_ylabel("row")
        plt.tight_layout()
        plt.show()
        #plt.pause(0.001)

    def compute_free_space_pct(self) -> float:
        """
        Computes the fraction of free cells in the entire grid.
        """
        rest = self.grid[GridChannels.RESTRICTION.value]
        total_cells = rest.size
        if total_cells == 0:
            return 1.0
        restricted = np.count_nonzero(rest)
        return 1.0 - (restricted / total_cells)


    def compute_actual_occupation(self) -> int:
        """
        Returns the number of cells currently occupied in the restriction layer.
        Overlaps count only once.
        """
        return int(np.count_nonzero(self.grid[GridChannels.RESTRICTION.value]))


    def compute_individual_sum(self) -> int:
        """
        Computes the sum of the individual occupation of each restriction,
        ignoring overlaps. This is done by stamping each restriction alone.
        """
        total = 0
        for restriction in self.restrictions.values():
            total += Stamp.occupation_in_cells(restriction, self.cell_size)
        return total


    def polygons(self):
        return [Stamp.to_world_polygon(r) for r in self.restrictions.values()]
    
    def to_geodataframe(self) -> gpd.GeoDataFrame:
        data = [
            {
                "id": r.id,
                "shape": r.shape.name,
                "radius": r.radius,
                "source": r.source.name,
                "rotation": r.rotation,
                "geometry": Stamp.to_world_polygon(r),
            }
            for r in self.restrictions.values()
        ]
        return gpd.GeoDataFrame(data, geometry="geometry", crs="EPSG:31983") #EPSG Meters

if __name__ == "__main__":
    """
    Teste local rápido:
    - Cria um mapa retangular sintético
    - Gera grid
    - Adiciona 3 restrições circulares (raio em metros)
    - Aplica e plota CITY_MASK e RESTRICTION
    """

    # 1) mapa retangular simples no CRS do grid (por ex. UTM 23S, metros)
    #    Aqui: um retângulo 10km x 8km
    #grid_crs = "EPSG:31983"
    rect = Polygon([(0, 0), (10_000, 0), (10_000, 8_000), (0, 8_000)])
    gdf = gpd.GeoDataFrame(geometry=[rect], crs="EPSG:31983")

    mgr = AirspaceGrid(gdf, cell_size=20)

    # 2) adiciona restrições – duas no CRS do grid e uma em lat/lon (exemplo fictício)
    #    (se você tiver lat/lon reais, troque location_epsg="EPSG:4326" e passe lon,lat)

    # TODO: FORÇAR O USO DO "EPSG:31983".
    r1 = mgr.add_restriction(
        shape=RestrictionShape.DISK,
        radius=1200,
        location=Point(2500, 2500),
        source=RestrictionSource.HELIPORT,
        rotation=0.0,
        location_epsg="EPSG:31983",
    )
    r2 = mgr.add_restriction(
        shape=RestrictionShape.CIRCULAR_SECTOR,
        radius=800,
        location=Point(7500, 3000),
        source=RestrictionSource.HELIPORT,
        location_epsg="EPSG:31983",
    )
    r3 = mgr.add_restriction(
        shape=RestrictionShape.CIRCULAR_SECTOR, #square not working
        radius=1000,
        location=Point(8000, 3000),
        source=RestrictionSource.UNKNOWN,
        location_epsg="EPSG:31983",
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


    
    
