

import time
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from skyweaver.core.logistics.depot import Depot
from skyweaver.grid.structure.hexgrid import HexGrid
from skyweaver.planning.graph_builder import GraphBuilder
from skyweaver.planning.logistics.planning_outpost import PlanningOutpost


Depot()

t0 = time.perf_counter()

# ---------------------------------------
# 1. Build grid and graph
# ---------------------------------------
t_grid_start = time.perf_counter()
grid = HexGrid(cell_size=100.0)
t_grid_end = time.perf_counter()

outpost = PlanningOutpost()
builder = GraphBuilder(outpost=outpost)

t_graph_start = time.perf_counter()
graph = builder.build_navigation_graph()
t_graph_end = time.perf_counter()

num_vertices = graph.vcount()
num_edges = graph.ecount()

# ---------------------------------------
# 2. Plot hex grid (background)
# ---------------------------------------
t_plot_hex_start = time.perf_counter()

fig, ax = plt.subplots(figsize=(10, 10))

for cell in grid.iter_domain_cells():
    poly = cell.polygon
    x, y = poly.exterior.xy

    patch = MplPolygon(
        list(zip(x, y)),
        closed=True,
        edgecolor="lightgray",
        facecolor="none",
        linewidth=0.6,
        alpha=0.6,
    )
    ax.add_patch(patch)

t_plot_hex_end = time.perf_counter()

# ---------------------------------------
# 3. Plot graph edges (foreground)
# ---------------------------------------
t_plot_edges_start = time.perf_counter()

vid_to_cell = graph["vertex_id_to_cell"]

for e in graph.es:
    v1, v2 = e.tuple

    c1 = vid_to_cell[v1]
    c2 = vid_to_cell[v2]

    assert c1 and c2

    x = [c1.cartesian_center.x, c2.cartesian_center.x]
    y = [c1.cartesian_center.y, c2.cartesian_center.y]

    ax.plot(x, y, color="blue", linewidth=1.0, alpha=0.8)

t_plot_edges_end = time.perf_counter()

# ---------------------------------------
# 4. Plot graph vertices
# ---------------------------------------
t_plot_vertices_start = time.perf_counter()

xs, ys = [], []
for cell in vid_to_cell.values():
    xs.append(cell.cartesian_center.x)
    ys.append(cell.cartesian_center.y)

ax.scatter(xs, ys, c="red", s=8, zorder=5)

t_plot_vertices_end = time.perf_counter()

# ---------------------------------------
# 5. Styling
# ---------------------------------------
ax.set_aspect("equal")
(xmin, xmax), (ymin, ymax) = grid.get_domain()
ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)
ax.set_title("HexGrid + iGraph overlay")
ax.grid(False)

t_total = time.perf_counter()
print(f"[TIME] TOTAL runtime: {t_total - t0:.3f}s")

plt.show()
