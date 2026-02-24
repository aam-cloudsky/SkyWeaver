import random

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from skyweaver.core.logistics.depot import Depot
from skyweaver.units.analysis.metrics import average_path_length, betweenness
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.routes.graph.graph_builder import GraphBuilder
from skyweaver.units.routes.graph.graph_pack import AirspaceGraphPack
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost
from skyweaver.units.routes.routing import Routing, compute_terminal_paths

random.seed(42)
depot = Depot()

# ======================================================
# 1. Build grid
# ======================================================
grid = HexGrid(cell_size=100.0)
all_cells = list(grid.iter_domain_cells())


def cell_xy(cell):
    """Explicit conversion: HexCell -> (x, y) in Cartesian coords."""
    c = grid.cartesian_cell_center(cell)
    return c.x, c.y


# ======================================================
# 2. Pick initial terminals
# ======================================================
available_cells = [c for c in all_cells if c.is_traversable]
NUM_TERMINALS = 3
terminals = random.sample(available_cells, NUM_TERMINALS)

# ======================================================
# 3. Randomly block cells (excluding terminals)
# ======================================================
BLOCK_RATIO = 0.15
NUM_HELIPORTS = 5
candidates = [c for c in all_cells if c not in terminals]
blocked = random.sample(candidates, int(len(candidates) * BLOCK_RATIO))

for c in blocked:
    c.set_restricted()

heliports = random.sample(blocked, min(NUM_HELIPORTS, len(blocked)))

# ======================================================
# 4. Build base graph (G0)
# ======================================================
outpost = RoutesOutpost()
builder = GraphBuilder(outpost=outpost)

base_graph: AirspaceGraphPack = builder.build_airspace_graph()
planner = Routing(base_graph)

# ======================================================
# 5. Matplotlib setup
# ======================================================
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect("equal")

bounds = grid.domain_bounds()
ax.set_xlim(bounds.min_x, bounds.max_x)
ax.set_ylim(bounds.min_y, bounds.max_y)

ax.set_title("Click to add/remove terminals")

# ======================================================
# 6. Plot hex grid
# ======================================================
cell_patches = {}
for cell in all_cells:
    poly = grid.cell_polygon(cell).exterior.coords
    face = "lightcoral" if not cell.is_traversable else "none"

    patch = MplPolygon(
        poly,
        closed=True,
        edgecolor="lightgray",
        facecolor=face,
        linewidth=0.8,
    )
    ax.add_patch(patch)
    cell_patches[cell] = patch

# ======================================================
# 7. Terminals + heliports (static artists)
# ======================================================
tx, ty = zip(*(cell_xy(c) for c in terminals)) if terminals else ([], [])
terminals_scatter = ax.scatter(
    tx,
    ty,
    c="green",
    s=140,
    zorder=7,
    label="Terminals",
)

hx, hy = zip(*(cell_xy(c) for c in heliports)) if heliports else ([], [])
heliports_scatter = ax.scatter(
    hx,
    hy,
    c="red",
    s=110,
    zorder=7,
    label="Heliports (restricted)",
)

mouse_point = ax.scatter(
    [],
    [],
    c="black",
    s=80,
    zorder=8,
    label="Mouse",
)

# ======================================================
# 8. Dynamic artists (routes + labels)
# ======================================================
dynamic_artists: list = []
apl_text = ax.text(
    0.02,
    0.98,
    "APL: 0.0",
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=10,
    bbox=dict(
        boxstyle="round,pad=0.25",
        facecolor="white",
        edgecolor="lightgray",
        alpha=0.9,
    ),
)


def clear_dynamic_artists():
    for artist in dynamic_artists:
        artist.remove()
    dynamic_artists.clear()


def recompute_and_draw():
    clear_dynamic_artists()

    if len(terminals) < 2:
        apl_text.set_text("APL: 0.0")
        fig.canvas.draw_idle()
        return

    paths = compute_terminal_paths(planner, terminals)
    if not paths:
        apl_text.set_text("APL: 0.0")
        fig.canvas.draw_idle()
        return

    routes_graph = builder.build_routes_graph(paths)
    g1 = routes_graph.graph

    # Draw edges
    for e in g1.es:
        v1, v2 = e.tuple
        c1 = g1.vs[v1]["cell"]
        c2 = g1.vs[v2]["cell"]

        x1, y1 = cell_xy(c1)
        x2, y2 = cell_xy(c2)

        (line,) = ax.plot(
            [x1, x2],
            [y1, y2],
            color="blue",
            linewidth=3.0,
            alpha=0.85,
            zorder=5,
        )
        dynamic_artists.append(line)

    # APL + betweenness
    apl_result = average_path_length(routes_graph)
    apl_text.set_text(f"APL: {apl_result:.3f}")

    betw_result = betweenness(routes_graph)
    for cell_v, value in betw_result.items():
        if value == 0:
            continue

        cx, cy = cell_xy(cell_v)
        txt = ax.text(
            cx,
            cy,
            f"{value}",
            fontsize=9,
            color="darkred",
            ha="center",
            va="center",
            zorder=9,
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                edgecolor="none",
                alpha=0.7,
            ),
        )
        dynamic_artists.append(txt)

    fig.canvas.draw_idle()


# ======================================================
# 9. Mouse move (hover)
# ======================================================
def on_mouse_move(event):
    if event.inaxes != ax or event.xdata is None or event.ydata is None:
        return

    cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
    if cell is None or not cell.is_traversable:
        return

    mx, my = cell_xy(cell)
    mouse_point.set_offsets([[mx, my]])
    fig.canvas.draw_idle()


# ======================================================
# 10. Mouse click (toggle terminal)
# ======================================================
def on_mouse_click(event):
    if event.inaxes != ax or event.button != 1:
        return
    if event.xdata is None or event.ydata is None:
        return

    cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
    if cell is None or not cell.is_traversable:
        return

    if cell in terminals:
        terminals.remove(cell)
    else:
        terminals.append(cell)

    if terminals:
        pts = np.array([cell_xy(c) for c in terminals], dtype=float)
    else:
        pts = np.empty((0, 2), dtype=float)

    terminals_scatter.set_offsets(pts)
    recompute_and_draw()


# ======================================================
# 10b. Right click (toggle restriction)
# ======================================================
def on_right_click(event):
    if event.inaxes != ax or event.button != 3:
        return
    if event.xdata is None or event.ydata is None:
        return

    cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
    if cell is None:
        return
    if cell in terminals:
        return

    if cell.is_traversable:
        cell.set_restricted()
        cell_patches[cell].set_facecolor("lightcoral")
    else:
        cell.set_available()
        cell_patches[cell].set_facecolor("none")

    # Rebuild airspace graph and planner after restriction change
    global base_graph, planner
    base_graph = builder.build_airspace_graph()
    planner = Routing(base_graph)

    recompute_and_draw()


# ======================================================
# 11. Connect callbacks
# ======================================================
fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
fig.canvas.mpl_connect("button_press_event", on_mouse_click)
fig.canvas.mpl_connect("button_press_event", on_right_click)

ax.legend()
recompute_and_draw()
plt.show()
