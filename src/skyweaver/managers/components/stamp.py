import numpy as np
from shapely.geometry import Polygon, Point
from typing import Dict, List, Tuple


class Stamp:
    """

    This class aims to create a faster way to rasterize a polygon. The idea is to create
    a stamp, where only the borders is stored. When rotated, it is applied the rotation matrix from numpy.
    It returns the grid with borders and interior fufilled.

    Its implementation were inspired on the paper “IDEAL: a Vector-Raster Hybrid Model for Efficient Spatial Queries
    over Complex Polygons” (MDM 2021) by Teng et al.  doi:10.1109/mdm52706.2021.00024

    The paper implementation can be found in: https://github.com/StonyBrookDB/IDEAL/tree/master.
    I tried to adapt the idea for my problem. The general idea is to identify the borders, and fufill the interior.
    Precomputed 'stamp' storing only border cells of a polygon
    for fast rotation and rasterization.

    Follows the core idea from the IDEAL paper:
    - Store only border cell coordinates (integer indices in the local grid)
    - On rotation: transform border cell centers, map to new indices
    - Fill interiors via scanline (row-wise toggle)

    The rasterization process consists of two main steps:
      1. Initial classification:
         - If the cell is fully within the polygon, mark as interior.
         - Else if the cell intersects the polygon boundary, mark as border, and save segments.
         - Else mark as exterior.

      2. Scanline fill:
         - For each row, toggles an 'in_region' flag each time a border cell is encountered.
         - Cells encountered while 'in_region' is True (and not already border) are marked interior.
         - This approximates filling the polygon interior following scanline rules.

    This structure allows:
      - O(1) checks for whether a point/cell is inside, outside, or on the boundary.
      - Reduction in shapely operations per cell, improving performance, especially in iterative loops.

      This class rasterizes a given Shapely polygon into a grid of cells based on a specified cell size.
    Each cell receives one of three status values:
      0 = exterior (outside the polygon),
      1 = border (intersects the polygon boundary),
      2 = interior (fully contained within the polygon).
    """

    def __init__(self, poly: Polygon, cell_size: float):
        self.poly = poly
        self.cell_size = cell_size
        self._precompute_stamp()

    def _precompute_stamp(self):
        """Pré-calcula células de borda e salva como coordenadas centrais (array)."""
        minx, miny, maxx, maxy = self.poly.bounds
        self.nx = int(np.ceil((maxx - minx) / self.cell_size))
        self.ny = int(np.ceil((maxy - miny) / self.cell_size))
        self.minx, self.miny = minx, miny

        border_points = []
        for iy in range(self.ny):
            for ix in range(self.nx):
                x0 = self.minx + ix * self.cell_size
                y0 = self.miny + iy * self.cell_size
                cell_poly = Polygon(
                    [
                        (x0, y0),
                        (x0 + self.cell_size, y0),
                        (x0 + self.cell_size, y0 + self.cell_size),
                        (x0, y0 + self.cell_size),
                    ]
                )

                if cell_poly.intersects(self.poly) and not cell_poly.within(self.poly):
                    cx = x0 + self.cell_size / 2
                    cy = y0 + self.cell_size / 2
                    border_points.append((cx, cy))

        self.border_points = np.array(border_points, dtype=np.float32)  # (N, 2)

    def rotated_mask(self, angle_rad: float) -> np.ndarray:
        """Gera máscara para o polígono rotacionado."""
        # Matriz de rotação
        c, s = np.cos(angle_rad), np.sin(angle_rad)
        rot_matrix = np.array([[c, -s], [s, c]], dtype=np.float32)

        # Rotaciona todos os pontos de borda (N, 2)
        rotated_points = self.border_points @ rot_matrix.T  # (N, 2)

        # Converte para índices (vetorizado)
        ix = np.floor((rotated_points[:, 0] - self.minx) / self.cell_size).astype(int)
        iy = np.floor((rotated_points[:, 1] - self.miny) / self.cell_size).astype(int)

        # Filtra índices válidos
        mask_valid = (ix >= 0) & (ix < self.nx) & (iy >= 0) & (iy < self.ny)
        ix, iy = ix[mask_valid], iy[mask_valid]

        # Cria máscara vazia
        mask = np.zeros((self.ny, self.nx), dtype=np.uint8)

        # Marca bordas
        mask[iy, ix] = 1

        # Preenche interiores (scanline IDEAL)
        for row in np.unique(iy):
            cols = np.where(mask[row] == 1)[0]
            if cols.size > 1:
                # Alterna preenchimento entre pares
                for start, end in zip(cols[::2], cols[1::2]):
                    mask[row, start + 1 : end] = 2

        return mask
