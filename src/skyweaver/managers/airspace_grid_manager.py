# src/skyweaver/managers/airspace_grid.py

import geopandas as gpd
import numpy as np
from shapely import unary_union
from shapely.geometry import Polygon, Point
from typing import Tuple, Optional
from skyweaver.dataclasses.restriction import Restriction
from skyweaver.enums.grid_channels import GridChannels
from pyproj import Transformer

import numpy as np

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
    ):
        """
        Initializes the airspace grid.

        Args:
            map: GeoDataFrame representing the region.
            resolution: Size of each cell in meters.
            crs: Coordinate reference system (e.g., EPSG code).
        """

        crs: str = "EPSG:31983"  # Default to UTM zone 23S for Brazil, in meters, adjust as needed.
        self.source_map: gpd.GeoDataFrame = source_map.to_crs(crs)
        self.cell_size = cell_size
        self.crs = crs
        self.grid = self._create_grid(cell_size=self.cell_size)
        self._init_layers()

        self.restrictions: list[Restriction] = []  # List to hold restriction polygons
        self._restriction_counter = 0

    def _next_id(self) -> int:
        current = self._restriction_counter
        self._restriction_counter += 1
        return current

    def add_restriction(self, shape: RestrictionShape, radius: float, location: Point, source: RestrictionSource = RestrictionSource.UNKNOWN, rotation: float = 0.0) -> int:
        """
        Adds a restriction polygon to the grid.
        """

        #TODO: LOCATION É BASEADO NA LATITUDE, LAT LON
        # COMO MOSTRADO AQUI, ALGO DO TIPO: "POINT (-42.991666666667 -22.915833333333)"
        # ASSIM PRECISA, POSTERIORMENTE, UM CONVERSOR DE LATITUDE/LONGITUDE PARA O CRS DO GRID

        restriction = Restriction(
            id=self._next_id(),
            shape=shape,
            radius=radius,
            source=source,
            location=location,
            rotation=rotation
        )
        self.restrictions.append(restriction)

        return restriction.id
    
    def remove_restriction(self, restriction_id: int) -> bool:
        """
        Removes a restriction polygon by its ID.
        """
        for i, restriction in enumerate(self.restrictions):
            if restriction.id == restriction_id:
                del self.restrictions[i]
                return True
        return False

    def _create_grid(self, cell_size: float) -> np.ndarray:
        minx, miny, maxx, maxy = self.source_map.total_bounds
        width = maxx - minx
        height = maxy - miny

        n_cols = int(np.ceil(width / cell_size))
        n_rows = int(np.ceil(height / cell_size))

        grid = np.zeros((len(GridChannels), n_rows, n_cols), dtype=np.int32)

        polygons = []
        for i in range(n_rows):
            for j in range(n_cols):
                x0 = minx + j * cell_size
                y0 = miny + i * cell_size
                poly = Polygon([
                    (x0, y0),
                    (x0 + cell_size, y0),
                    (x0 + cell_size, y0 + cell_size),
                    (x0, y0 + cell_size)
                ])
                polygons.append(poly)

        cells_gdf = gpd.GeoDataFrame(geometry=polygons, crs=self.crs)
        mask = cells_gdf.intersects(unary_union(self.source_map.geometry))
        grid[GridChannels.VALIDITY_MASK.value] = mask.to_numpy().reshape(
            (n_rows, n_cols)).astype(np.int32)

        return grid
    
    def reset_grid(self):
        """
        Resets the grid to its initial state.
        """
        self.grid = self._create_grid(cell_size=self.cell_size)
        self._init_layers()

    def apply_restrictions(self):
        """
        Applies all registered restriction masks to the grid.
        """

        #TODO: REVER ESSA FUNÇÃO. NÃO TENHO CERTEZA SE ELA ESTÁ CORRETA.
        # A RESTRIÇÃO PODE ULTRAPASSAR OS LIMITES DO SOURCE_MAP, ASSIM O GRID TEM QUE SER MAIOR DO QUE O SOURCE_MAP 
        # EM AO MENOS 2 MILHAS (3704 METROS) PARA CADA LADO (NOS SEUS LIMITES).

        # TODO: LOCATION É BASEADO NA LATITUDE, LAT LON
        # COMO MOSTRADO AQUI, ALGO DO TIPO: "POINT (-42.991666666667 -22.915833333333)"
        # ASSIM PRECISA, POSTERIORMENTE, UM CONVERSOR DE LATITUDE/LONGITUDE PARA O CRS DO GRID


        for restriction in self.restrictions:
            mask = restriction.to_cell_mask(self.cell_size)  # (h, w)
            h, w = mask.shape


            row, col = self.point_to_cell(restriction.location)

            # Top-left do patch onde a máscara será aplicada
            top = row - h // 2
            left = col - w // 2

            # Aplicar no canal "restricted" (canal 1, por ex.) — você pode mudar isso
            channel = GridChannels.RESTRICTION.value

            for i in range(h):
                for j in range(w):
                    grid_i = top + i
                    grid_j = left + j

                    # Verifica se está dentro dos limites da grade
                    if (
                        0 <= grid_i < self.grid.shape[1]
                        and 0 <= grid_j < self.grid.shape[2]
                        and mask[i, j] == 1
                    ):
                        # Marcar célula como restrita
                        self.grid[channel, grid_i, grid_j] = 1



    def to_geodataframe(self) -> Optional[gpd.GeoDataFrame]:
        # Unite restrictions, grid, map, and other layers into a single GeoDataFrame
        if self.grid is None:
            return None
        return gpd.GeoDataFrame(self.grid)

    def _init_layers(self):
        """
        Inicializa colunas extras do grid, como 'restricted'.
        """
        self.grid["restricted"] = False
        # Futuro: self.grid["elevation"] = ...
        # Futuro: self.grid["risk_level"] = ...

    def point_to_cell(self, point: Point) -> Optional[Tuple[int, int]]:
        minx, miny, _, _ = self.source_map.total_bounds
        col = int((point.x - minx) // self.cell_size)
        row = int((point.y - miny) // self.cell_size)
        if 0 <= row < self.grid.shape[1] and 0 <= col < self.grid.shape[2]:
            return row, col
        return None

