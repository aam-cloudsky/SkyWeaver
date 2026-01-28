from skyweaver.grid.structure.hexgrid import HexGrid
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

# ------------------------------------------------------------
# 3. Plot origin to validate alignment
# ------------------------------------------------------------
ax.plot(0, 0, "ro", label="Cartesian origin (0,0)")
origin_cell = grid.get_cell_from_cartesian(0, 0)

if origin_cell:
    ox, oy = origin_cell.cartesian_center.x, origin_cell.cartesian_center.y
    ax.plot(ox, oy, "bx", label="HexCoord(0,0) center")

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
ax.set_title(
    f"HexGrid validation (pointy-top, size = {grid.outpost.grid_parcel.cell_size})")

plt.show()
