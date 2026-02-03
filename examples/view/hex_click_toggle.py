import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from skyweaver.grid.structure.hexgrid import HexGrid
from skyweaver.grid.geometry.hexcell import HexCell


# ======================================================
# Setup
# ======================================================

grid = HexGrid(cell_size=100.0)
cells = list(grid.iter_domain_cells())

fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect("equal")

(xmin, xmax), (ymin, ymax) = grid.get_domain()
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

ax.set_title("HexGrid – click to toggle restriction")

# ======================================================
# Draw grid and keep mapping cell -> patch
# ======================================================

cell_to_patch: dict[HexCell, MplPolygon] = {}

for cell in cells:
    poly = list(cell.polygon.exterior.coords)

    patch = MplPolygon(
        poly,
        closed=True,
        edgecolor="black",
        facecolor="none",     # available
        linewidth=0.8,
        zorder=1,
    )

    ax.add_patch(patch)
    cell_to_patch[cell] = patch

# ======================================================
# Mouse callback
# ======================================================


def on_mouse_click(event):
    if event.inaxes != ax:
        return
    if event.xdata is None or event.ydata is None:
        return

    # Only LEFT click
    if event.button != 1:
        return

    cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
    if cell is None:
        return

    patch = cell_to_patch.get(cell)
    if patch is None:
        return

    # TOGGLE availability
    if cell.available:
        cell.set_unavailable()
        patch.set_facecolor("lightcoral")
    else:
        cell.set_available()
        patch.set_facecolor("none")

    fig.canvas.draw_idle()


# ======================================================
# Connect & show
# ======================================================

fig.canvas.mpl_connect("button_press_event", on_mouse_click)
plt.show()
