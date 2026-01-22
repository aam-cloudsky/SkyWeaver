from math import ceil, floor
from typing import List, Optional, Tuple

from shapely import Point
from skyweaver.discretization.grid.base_cell import BaseCell
from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.grid.hexgrid.hexgrid_configuration import (
    HexGridConfiguration,
)

from typing import Dict, Iterable
from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.grid.hexgrid.hexcell import HexCell

from skyweaver.discretization.grid.hexgrid.hexprojection import (
    pixel_to_pointy_hex,
    pixel_to_pointy_hex_frac,
    pointy_hex_to_pixel,
)

from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord
from skyweaver.discretization.grid.hexgrid.hexcell import HexCell
from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.instance_segmentation.geometry.cluster import Cluster


from skyweaver.discretization.grid.base_grid import BaseGrid
from skyweaver.discretization.grid.hexgrid.hextopology import neighbors as hexgrid_neighbors
from skyweaver.discretization.grid.hexgrid.hexcoord import HexCoord
from typing import Dict

from skyweaver.discretization.grid.hexgrid.hextopology import hex_distance
class HexGrid(BaseGrid):
    """
    Container for hexagonal cells indexed by HexCoord.
    Geometry and topology are handled by other modules.
    """

    def __init__(self, cell_size: float = 1.0):

        self.config: HexGridConfiguration = HexGridConfiguration()
        self._cells: Dict[HexCoord, HexCell] = {}

        # self._cell_size: float = cell_size
        with self.config:
            self.config.cell_size = cell_size
            self.config.grid = self

    # =======================================================
    # Private Functions
    # =======================================================

    def _create_cell(self, coord: HexCoord) -> HexCell:
        cell = HexCell(coord=coord, size=self.config.cell_size)
        cell.set_available() if self._compute_availability(cell) else cell.set_unavailable()

        self._cells[coord] = cell
        return cell

    def get_cell_from_coord(self, coord: HexCoord) -> Optional[HexCell]:
        if not self._coord_inside_domain(
            coord, self.config.cell_size, self.config.domain
        ):
            return None

        cell = self._cells.get(coord)
        if cell is None:
            cell = self._create_cell(coord)

        return cell

    def _is_within_risky_area(self, cell: HexCell, cluster: Cluster) -> bool:
        """Check if the cell is within the risky area of the cluster."""
        cell_center = cell.cartesian_center
        centroid = cluster.centroid

        vector = cell_center - centroid
        distance = vector.length

        return cluster.boundary_max_distance + cell.size >= distance

    def _verify_distance(
        self, point_a: Point, point_b: Point, threshold: float
    ) -> bool:
        """Check if the distance between two points is within a threshold."""
        return point_a.distance(point_b) <= threshold

    def _compute_availability(self, cell: HexCell) -> bool:
        for cluster in self.config.clusters:

            # Fast rejection
            if not self._is_within_risky_area(cell, cluster):
                continue

            # Expensive geometry check
            if cluster.intersection_area(cell.polygon) > 0:
                return False

        return True

    # =======================================================
    # Static Methods
    # =======================================================

    @staticmethod
    def _inside_domain(
        x: float,
        y: float,
        domain: tuple[tuple[float, float], tuple[float, float]],
    ) -> bool:
        (xmin, xmax), (ymin, ymax) = domain
        return xmin <= x <= xmax and ymin <= y <= ymax

    @staticmethod
    def _coord_inside_domain(
        coord: HexCoord,
        size: float,
        domain: tuple[tuple[float, float], tuple[float, float]],
    ) -> bool:
        x, y = pointy_hex_to_pixel(coord, size=size)
        (xmin, xmax), (ymin, ymax) = domain
        return xmin <= x <= xmax and ymin <= y <= ymax

    # =======================================================
    # Abstract Methods Implementation
    # TODO: better title
    # =======================================================

    def get_domain(self) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        return self.config.domain

    def get_cell_from_cartesian(self, x: float, y: float) -> Optional[HexCell]:
        coord = pixel_to_pointy_hex(x, y, self.config.cell_size)

        return self.get_cell_from_coord(coord)

    def iter_domain_cells(self) -> Iterable[HexCell]:
        """
        Lazily iterate over all hex cells inside the domain.

        Cells are created on-demand during iteration.
        Intended for debugging / visualization only.
        """
        (xmin, xmax), (ymin, ymax) = self.config.domain
        size = self.config.cell_size

        corners = [
            pixel_to_pointy_hex_frac(xmin, ymin, size),
            pixel_to_pointy_hex_frac(xmin, ymax, size),
            pixel_to_pointy_hex_frac(xmax, ymin, size),
            pixel_to_pointy_hex_frac(xmax, ymax, size),
        ]

        q_vals = [c[0] for c in corners]
        r_vals = [c[1] for c in corners]

        q_min = floor(min(q_vals))
        q_max = ceil(max(q_vals))
        r_min = floor(min(r_vals))
        r_max = ceil(max(r_vals))

        for q in range(q_min, q_max + 1):
            for r in range(r_min, r_max + 1):
                cell = self.get_cell_from_coord(HexCoord(q, r))
                if cell is not None:
                    #print(f"Yielding cell at HexCoord({q}, {r})")
                    yield cell

    def neighbors(self, cell: HexCell) -> List[BaseCell]:
        coords = hexgrid_neighbors(cell.coord)

        neighborhood: list[BaseCell] = []
        for c in coords:
            nb = self.get_cell_from_coord(c)
            if nb is not None:
                neighborhood.append(nb)

        return neighborhood 

    def lower_bound_steps(self, a: HexCell, b: HexCell) -> float:
        """Estimate the minimum number of steps between two cells"""

        min_distance: int = hex_distance(a.coord, b.coord)
        return min_distance  # Default implementation; override in subclasses
        

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    # ------------------------------------------------------------
    # 1. Build a simple configuration
    # ------------------------------------------------------------

    grid = HexGrid(cell_size=100.0)
    cells = grid.iter_domain_cells()

    # print(f"Generated hex grid with {len(cells)} cells.")
    # ------------------------------------------------------------
    # 2. Plot the hex grid
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 8))

    for cell in cells:
        poly = cell.polygon
        x, y = poly.exterior.xy

        patch = MplPolygon(
            list(zip(x, y)),
            closed=True,
            edgecolor="black",
            facecolor="none",
            linewidth=0.8,
        )
        ax.add_patch(patch)

        # Optional: plot axial coordinates at center (debug)
        cx, cy = cell.cartesian_center.x, cell.cartesian_center.y
        ax.text(
            cx,
            cy,
            f"({cell.coord.q},{cell.coord.r})",
            ha="center",
            va="center",
            fontsize=6,
            alpha=0.4,
        )

    print("Plotted hex grid.")
    # ------------------------------------------------------------
    # 3. Plot origin to validate alignment
    # ------------------------------------------------------------
    ax.plot(0, 0, "ro", label="Cartesian origin (0,0)")
    origin_cell = grid.get_cell_from_cartesian(0, 0)

    if origin_cell:
        ox, oy = origin_cell.cartesian_center.x, origin_cell.cartesian_center.y
        ax.plot(ox, oy, "bx", label="HexCoord(0,0) center")

    print("Plotted origin validation.")

    # ------------------------------------------------------------
    # 4. Plot styling
    # ------------------------------------------------------------
    ax.set_aspect("equal")

    (xmin, xmax), (ymin, ymax) = grid.get_domain()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.grid(False)
    ax.grid(False)
    ax.legend()
    ax.set_title(f"HexGrid validation (pointy-top, size = {grid.config.cell_size})")

    plt.show()



