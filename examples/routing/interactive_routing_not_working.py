import random
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from skyweaver.core.logistics.depot import Depot
from skyweaver.grid.structure.hexgrid import HexGrid

from skyweaver.planning.graph.graph_builder import GraphBuilder
from skyweaver.planning.logistics.planning_outpost import PlanningOutpost
from skyweaver.planning.routing import Routing, compute_terminal_paths

from skyweaver.visualization.logistics.viz_outpost import VizOutpost
from skyweaver.planning.logistics.planning_parcel import PlanningParcel
from skyweaver.grid.logistics.grid_parcel import GridParcel


"""
EXPERIMENTAL – visualization spike
Kept for future reference.
Not part of core architecture.
"""

# ======================================================
# Setup
# ======================================================
random.seed(42)
depot = Depot()

grid = HexGrid(cell_size=100.0)
all_cells = list(grid.iter_domain_cells())

available_cells = [c for c in all_cells if c.available]
fixed_terminals = random.sample(available_cells, 3)
fixed_terminal_set = set(fixed_terminals)

# Random blocks
blocked = random.sample(
    [c for c in all_cells if c not in fixed_terminal_set],
    int(len(all_cells) * 0.15),
)
for c in blocked:
    c.set_unavailable()


# ======================================================
# Outpost + Planner
# ======================================================
viz_outpost = VizOutpost()

builder = GraphBuilder(outpost=PlanningOutpost())

base_graph = builder.build_airspace_graph()
planner = Routing(base_graph.graph)


# ======================================================
# Matplotlib setup
# ======================================================
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect("equal")

(xmin, xmax), (ymin, ymax) = grid.get_domain()
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

ax.set_title("Reactive Routing Visualization")

# Static grid
for cell in all_cells:
    poly = cell.polygon.exterior.coords
    face = "lightcoral" if not cell.available else "none"

    ax.add_patch(
        MplPolygon(
            poly,
            closed=True,
            edgecolor="lightgray",
            facecolor=face,
            linewidth=0.8,
        )
    )

# Fixed terminals
ax.scatter(
    [c.cartesian_center.x for c in fixed_terminals],
    [c.cartesian_center.y for c in fixed_terminals],
    c="green",
    s=140,
    zorder=7,
    label="Fixed terminals",
)

mouse_point = ax.scatter([], [], c="black", s=80, zorder=8)
dynamic_artists: list = []


# ======================================================
# Snapshot callback (CORE)
# ======================================================
def on_state_sync(pallet: dict):
    """
    Called whenever VizOutpost receives a new consistent snapshot.
    """

    planning_parcel: PlanningParcel | None = pallet.get(PlanningParcel)
    grid_parcel: GridParcel | None = pallet.get(GridParcel)

    if not planning_parcel or not planning_parcel.terminal_graph:
        return

    g2 = planning_parcel.terminal_graph

    # Clear previous drawings
    for artist in dynamic_artists:
        artist.remove()
    dynamic_artists.clear()

    # Plot edges
    for e in g2.es:
        v1, v2 = e.tuple
        c1 = g2.vs[v1]["cell"]
        c2 = g2.vs[v2]["cell"]

        (line,) = ax.plot(
            [c1.cartesian_center.x, c2.cartesian_center.x],
            [c1.cartesian_center.y, c2.cartesian_center.y],
            color="blue",
            linewidth=3.0,
            alpha=0.85,
            zorder=5,
        )
        dynamic_artists.append(line)

    fig.canvas.draw_idle()


viz_outpost.set_on_pallet_sync(on_state_sync)


# ======================================================
# Mouse = intention publisher
# ======================================================
def on_mouse_move(event):
    if event.inaxes != ax or event.xdata is None or event.ydata is None:
        return

    cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)

    if cell is None or not cell.available or cell in fixed_terminal_set:
        return

    mouse_point.set_offsets([[cell.cartesian_center.x, cell.cartesian_center.y]])

    terminals = fixed_terminals + [cell]

    # Compute paths
    paths = compute_terminal_paths(planner, terminals)
    if not paths:
        return

    # Build terminal graph
    g2_pack = builder.build_terminals_graph([(p, 0.0) for p in paths])
    g2 = g2_pack.graph

    # Publish snapshot
    with viz_outpost:
        viz_outpost.planning_parcel.terminal_graph = g2


fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
ax.legend()
plt.show()
