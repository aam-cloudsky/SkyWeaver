from __future__ import annotations

import heapq
from typing import Any, Dict, List, Optional, Tuple, Callable

from skyweaver.planning.search_space.search_space import SearchSpace


CostFn = Callable[[Any, Any], float]
StopFn = Callable[[Any, float], bool]


class AStar:
    """
    Generic A* path planning algorithm.

    - Geometry-agnostic
    - Grid-agnostic
    - Ready for bounded and multi-target extensions
    """

    def __init__(
        self,
        space: SearchSpace,
        cost_fn: Optional[CostFn] = None,
    ):
        self.space = space
        self.cost_fn = cost_fn or (lambda a, b: 1.0)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------
    def search(
        self,
        start: Any,
        goal: Any,
        *,
        stop_fn: Optional[StopFn] = None,
    ) -> Optional[List[Any]]:
        """
        Standard single-goal A* search.
        """

        came_from, g_score = self._run(
            start=start,
            goal=goal,
            stop_fn=stop_fn,
        )

        if goal not in came_from and goal != start:
            return None

        return self._reconstruct_path(came_from, goal)

    # ------------------------------------------------------------
    # Core A* loop (reusable)
    # ------------------------------------------------------------
    def _run(
        self,
        start: Any,
        goal: Any,
        stop_fn: Optional[StopFn],
    ) -> Tuple[Dict[Any, Any], Dict[Any, float]]:
        """
        Core A* expansion loop.
        Returns search tree and g-scores.
        """

        open_heap: List[Tuple[float, int, Any]] = []
        came_from: Dict[Any, Any] = {}
        g_score: Dict[Any, float] = {start: 0.0}
        closed_set = set()

        counter = 0
        f_start = self.space.heuristic(start, goal)
        heapq.heappush(open_heap, (f_start, counter, start))

        while open_heap:
            f_current, _, current = heapq.heappop(open_heap)

            if current in closed_set:
                continue

            closed_set.add(current)

            # Optional external stopping logic (bounds, envelopes, etc.)
            if stop_fn and stop_fn(current, g_score[current]):
                continue

            if current == goal:
                break

            for neighbor in self.space.successors(current):
                tentative_g = g_score[current] + \
                    self.cost_fn(current, neighbor)

                if tentative_g >= g_score.get(neighbor, float("inf")):
                    continue

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                f_score = tentative_g + self.space.heuristic(neighbor, goal)
                counter += 1
                heapq.heappush(open_heap, (f_score, counter, neighbor))

        return came_from, g_score

    # ------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------
    @staticmethod
    def _reconstruct_path(
        came_from: Dict[Any, Any],
        goal: Any,
    ) -> List[Any]:
        path = [goal]
        while goal in came_from:
            goal = came_from[goal]
            path.append(goal)

        path.reverse()
        return path
    
if __name__ == "__main__":
    # ------------------------------------------------------------
    # Interactive A* + HexGrid visualization
    # ------------------------------------------------------------

    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon

    from skyweaver.discretization.grid.hexgrid.hexgrid import HexGrid
    from skyweaver.planning.search_space.hexgrid_search_space import (
        HexGridSearchSpace,
    )

    # ------------------------------------------------------------
    # 1. Build grid
    # ------------------------------------------------------------
    grid = HexGrid(cell_size=1.0)

    # ------------------------------------------------------------
    # 2. Wrap grid as SearchSpace
    # ------------------------------------------------------------
    space = HexGridSearchSpace(grid)

    # ------------------------------------------------------------
    # 3. Planner
    # ------------------------------------------------------------
    planner = AStar(space)

    # ------------------------------------------------------------
    # 4. Start position (fixed)
    # ------------------------------------------------------------
    start_cell = grid.get_cell_from_cartesian(0.0, 0.0)
    if start_cell is None:
        raise RuntimeError("Start outside grid domain")

    start = start_cell.coord

    # ------------------------------------------------------------
    # 5. Matplotlib figure
    # ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 10))

    # ------------------------------------------------------------
    # 6. Plot hex grid
    # ------------------------------------------------------------
    for cell in grid.iter_domain_cells():
        poly = cell.polygon
        x, y = poly.exterior.xy

        patch = MplPolygon(
            list(zip(x, y)),
            closed=True,
            edgecolor="black",
            facecolor="none",
            linewidth=0.5,
            alpha=0.6,
        )
        ax.add_patch(patch)

    # ------------------------------------------------------------
    # 7. Start marker
    # ------------------------------------------------------------
    start_center = start_cell.cartesian_center
    ax.plot(
        start_center.x,
        start_center.y,
        "go",
        markersize=10,
        label="Start",
        zorder=6,
    )

    # ------------------------------------------------------------
    # 8. Path & goal artists (initialized empty)
    # ------------------------------------------------------------
    (path_line,) = ax.plot([], [], "-r", linewidth=2.5, zorder=5, label="A* path")
    (goal_dot,) = ax.plot([], [], "bo", markersize=8, label="Goal", zorder=6)

    arrow_artist = {"ann": None}
    last_goal = {"coord": None}

    # ------------------------------------------------------------
    # 9. Mouse-move callback (dynamic replanning)
    # ------------------------------------------------------------
    def on_mouse_move(event):
        if event.xdata is None or event.ydata is None:
            return

        cell = grid.get_cell_from_cartesian(event.xdata, event.ydata)
        if cell is None or not cell.navigable:
            return

        goal = cell.coord
        if goal == last_goal["coord"]:
            return

        last_goal["coord"] = goal  # type: ignore

        path = planner.search(start, goal)
        if path is None or len(path) < 2:
            return

        xs, ys = [], []
        for coord in path:
            c = grid._get_cell_from_coord(coord)
            if c is None:
                continue
            center = c.cartesian_center
            xs.append(center.x)
            ys.append(center.y)

        # Update path
        path_line.set_data(xs, ys)

        # Update goal marker
        goal_dot.set_data([xs[-1]], [ys[-1]])

        # Remove old arrow
        if arrow_artist["ann"] is not None:
            arrow_artist["ann"].remove()

        # Add arrow pointing to goal
        arrow_artist["ann"] = ax.annotate(  # type: ignore
            "",
            xy=(xs[-1], ys[-1]),
            xytext=(xs[-2], ys[-2]),
            arrowprops=dict(
                arrowstyle="->",
                color="red",
                linewidth=2.5,
            ),
            zorder=7,
        )

        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)

    # ------------------------------------------------------------
    # 10. Plot formatting
    # ------------------------------------------------------------
    ax.set_aspect("equal")
    (xmin, xmax), (ymin, ymax) = grid.get_domain()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_title("Interactive HexGrid A* (hover to change goal)")
    ax.legend()
    ax.grid(False)

    plt.show()
