
import random
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from skyweaver.core.logistics.depot import Depot
from skyweaver.grid.structure.hexgrid import HexGrid
from skyweaver.planning.logistics.planning_outpost import PlanningOutpost
from skyweaver.planning.graph_builder import GraphBuilder
from skyweaver.planning.routing import Routing, compute_terminal_paths

random.seed(42)
depot = Depot()
# ======================================================
# 1. Build grid
# ======================================================
grid = HexGrid(cell_size=100.0)
all_cells = list(grid.iter_domain_cells())

# ======================================================
# 2. Pick fixed terminals
# ======================================================
available_cells = [c for c in all_cells if c.available]
NUM_TERMINALS = 3
fixed_terminals = random.sample(available_cells, NUM_TERMINALS)
fixed_terminal_set = set(fixed_terminals)

# ======================================================
# 3. Randomly block cells (excluding terminals)
# ======================================================
BLOCK_RATIO = 0.15
candidates = [c for c in all_cells if c not in fixed_terminal_set]
blocked = random.sample(candidates, int(len(candidates) * BLOCK_RATIO))

for c in blocked:
    c.set_unavailable()

# ======================================================
# 4. Build base graph (G0)
# ======================================================
outpost = PlanningOutpost()
builder = GraphBuilder(outpost=outpost)

base_graph = builder.build_navigation_graph()
planner = Routing(base_graph)

# ======================================================
# 5. Matplotlib setup
# ======================================================
fig, ax = plt.subplots(figsize=(10, 10))
ax.set_aspect("equal")

(xmin, xmax), (ymin, ymax) = grid.get_domain()
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

ax.set_title("Dynamic paths graph (G1 → G2) with betweenness")

# ======================================================
# 6. Plot hex grid
# ======================================================
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

# ======================================================
# 7. Plot fixed terminals
# ======================================================
ax.scatter(
    [c.cartesian_center.x for c in fixed_terminals],
    [c.cartesian_center.y for c in fixed_terminals],
    c="green",
    s=140,
    zorder=7,
    label="Fixed terminals",
)

# ======================================================
# 8. Dynamic artists
# ======================================================
dynamic_artists: list = []

mouse_point = ax.scatter(
    [],
    [],
    c="black",
    s=80,
    zorder=8,
    label="Mouse terminal",
)

# ======================================================
# 9. Mouse callback
# ======================================================
def on_mouse_move(event):
    if event.inaxes != ax or event.xdata is None or event.ydata is None:
        return

    cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)

    if (
        cell is None
        or not cell.available
        or cell in fixed_terminal_set
    ):
        return

    # Update mouse marker
    mouse_point.set_offsets([
        [cell.cartesian_center.x, cell.cartesian_center.y]
    ])

    # Clear previous drawings
    for artist in dynamic_artists:
        artist.remove()
    dynamic_artists.clear()

    terminals = fixed_terminals + [cell]

    # --------------------------------------------------
    # Compute terminal paths (G0 → G1)
    # --------------------------------------------------
    t0 = time.perf_counter()
    paths = compute_terminal_paths(planner, terminals)

    if not paths:
        fig.canvas.draw_idle()
        return

    # --------------------------------------------------
    # Build paths graph (G1 → G2)
    # --------------------------------------------------
    g2 = builder.build_path_induced_graph(paths)

    # --------------------------------------------------
    # Plot G2 edges
    # --------------------------------------------------
    for e in g2.es:
        v1, v2 = e.tuple
        c1 = g2.vs[v1]["cell"]
        c2 = g2.vs[v2]["cell"]

        xs = [c1.cartesian_center.x, c2.cartesian_center.x]
        ys = [c1.cartesian_center.y, c2.cartesian_center.y]

        line, = ax.plot(
            xs,
            ys,
            color="blue",
            linewidth=3.0,
            alpha=0.85,
            zorder=5,
        )
        dynamic_artists.append(line)

    # --------------------------------------------------
    # Betweenness (intermediates only)
    # --------------------------------------------------
    bet = g2.betweenness()

    for v, b in zip(g2.vs, bet):

        if v["is_terminal"]:
            continue

        cell_v = v["cell"]

        txt = ax.text(
            cell_v.cartesian_center.x,
            cell_v.cartesian_center.y,
            f"{b:.2f}",
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
            )
        )
        dynamic_artists.append(txt)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    print(f"[UPDATE] {dt_ms:.2f} ms")

    fig.canvas.draw_idle()

# ======================================================
# 10. Connect mouse
# ======================================================
fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
ax.legend()
plt.show()
