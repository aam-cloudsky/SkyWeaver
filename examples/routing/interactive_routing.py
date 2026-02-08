import random
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from skyweaver.core.logistics.depot import Depot
from skyweaver.units.analysis.metrics import average_path_length, betweenness
from skyweaver.units.grid.structure.hexgrid import HexGrid
from skyweaver.units.routes.graph.graph_builder import GraphBuilder
from skyweaver.units.routes.graph.graph_pack import AirspaceGraphPack
from skyweaver.units.routes.logistics.routes_outpost import RoutesOutpost
from skyweaver.units.routes.planning.routing import Routing, compute_terminal_paths

random.seed(42)
depot = Depot()

# ======================================================
# 1. Build grid
# ======================================================
grid = HexGrid(cell_size=100.0)
all_cells = list(grid.iter_domain_cells())

# ======================================================
# 2. Pick initial terminals
# ======================================================
available_cells = [c for c in all_cells if c.available]
NUM_TERMINALS = 3
terminals = random.sample(available_cells, NUM_TERMINALS)

# ======================================================
# 3. Randomly block cells (excluding terminals)
# ======================================================
BLOCK_RATIO = 0.15
candidates = [c for c in all_cells if c not in terminals]
blocked = random.sample(candidates, int(len(candidates) * BLOCK_RATIO))

for c in blocked:
    c.set_unavailable()

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

(xmin, xmax), (ymin, ymax) = grid.get_domain()
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

ax.set_title("Click to add/remove terminals")

# ======================================================
# 6. Plot hex grid
# ======================================================
cell_patches = {}
for cell in all_cells:
    poly = cell.polygon.exterior.coords
    face = "lightcoral" if not cell.available else "none"

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
# 7. Terminals state
# ======================================================
terminals_scatter = ax.scatter(
    [c.cartesian_center.x for c in terminals],
    [c.cartesian_center.y for c in terminals],
    c="green",
    s=140,
    zorder=7,
    label="Terminals",
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
        fig.canvas.draw()
        return

    paths = compute_terminal_paths(planner, terminals)
    if not paths:
        apl_text.set_text("APL: 0.0")
        fig.canvas.draw()
        return

    routes_graph = builder.build_routes_graph(paths)
    g1 = routes_graph.graph

    # Draw edges
    for e in g1.es:
        v1, v2 = e.tuple
        c1 = g1.vs[v1]["cell"]
        c2 = g1.vs[v2]["cell"]

        xs = [c1.cartesian_center.x, c2.cartesian_center.x]
        ys = [c1.cartesian_center.y, c2.cartesian_center.y]

        (line,) = ax.plot(
            xs,
            ys,
            color="blue",
            linewidth=3.0,
            alpha=0.85,
            zorder=5,
        )
        dynamic_artists.append(line)

    terminals_graph = builder.build_terminals_graph(paths)
    apl_result = average_path_length(base_graph, routes_graph, terminals_graph)
    apl_text.set_text(f"APL: {apl_result.value:.3f}")

    betw_result = betweenness(base_graph, routes_graph, terminals_graph)
    for cell_v, value in betw_result.values.items():
        if value == 0:
            continue
        txt = ax.text(
            cell_v.cartesian_center.x,
            cell_v.cartesian_center.y,
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
    if cell is None or not cell.available:
        return

    mouse_point.set_offsets([[cell.cartesian_center.x, cell.cartesian_center.y]])
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
    if cell is None or not cell.available:
        return

    if cell in terminals:
        terminals.remove(cell)
    else:
        terminals.append(cell)

    pts = np.array(
        [[c.cartesian_center.x, c.cartesian_center.y] for c in terminals],
        dtype=float,
    )
    if pts.size == 0:
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

    if cell.available:
        cell.set_unavailable()
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
