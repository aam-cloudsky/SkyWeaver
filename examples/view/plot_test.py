from dataclasses import dataclass
from typing import Optional, Literal

import plotly.graph_objects as go

from skyweaver.core.logistics.depot import Depot
from skyweaver.grid.structure.hexgrid import HexGrid
from skyweaver.grid.geometry.hexcell import HexCell
from skyweaver.grid.geometry.hexcoord import HexCoord


# ============================================================
# IHM Event Model
# ============================================================

MouseEventType = Literal["press", "release"]


@dataclass(frozen=True)
class HexMouseEvent:
    coord: HexCoord
    event_type: MouseEventType
    x: float
    y: float


# ============================================================
# Plotly HexGrid IHM (FigureWidget-based)
# ============================================================

class HexGridPlotlyIHM:
    """
    Pure UI component.

    Uses Plotly FigureWidget to capture mouse events.
    """

    def __init__(self, grid: HexGrid):
        self.grid = grid
        self.fig = go.FigureWidget()
        self._last_press_cell: Optional[HexCoord] = None

        self._build_figure()

    # ------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------
    
    def _build_figure(self):
        cells = list(self.grid.iter_domain_cells())

        for cell in cells:
            self._add_cell_trace(cell)

        (xmin, xmax), (ymin, ymax) = self.grid.get_domain()

        self.fig.update_layout(
            width=800,
            height=800,
            xaxis=dict(range=[xmin, xmax], scaleanchor="y"),
            yaxis=dict(range=[ymin, ymax]),
            title="HexGrid IHM (Plotly)",
            showlegend=False,
        )

    def _add_cell_trace(self, cell: HexCell):
        poly = list(cell.polygon.exterior.coords)
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]

        trace = go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line=dict(color="black", width=1),
            hoverinfo="none",
        )

        self.fig.add_trace(trace)

        # Attach callback to THIS trace
        trace.on_click(self._make_click_handler(cell))

    # ------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------

    def _make_click_handler(self, cell: HexCell):
        def handler(trace, points, selector):
            if not points.xs or not points.ys:
                return

            x = points.xs[0]
            y = points.ys[0]

            if self._last_press_cell is None:
                self._last_press_cell = cell.coord
                event = HexMouseEvent(
                    coord=cell.coord,
                    event_type="press",
                    x=x,
                    y=y,
                )
            else:
                event = HexMouseEvent(
                    coord=cell.coord,
                    event_type="release",
                    x=x,
                    y=y,
                )
                self._last_press_cell = None

            self.on_hex_event(event)

        return handler

    # ------------------------------------------------------------
    # Output hook
    # ------------------------------------------------------------

    def on_hex_event(self, event: HexMouseEvent):
        print(
            f"[IHM] Hex {event.coord} | "
            f"{event.event_type.upper()} | "
            f"x={event.x:.1f}, y={event.y:.1f}"
        )

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def show(self):
        return self.fig


# ============================================================
# Example usage
# ============================================================

def main():
    Depot()
    grid = HexGrid(cell_size=100.0)
    ihm = HexGridPlotlyIHM(grid)
    ihm.show()


if __name__ == "__main__":
    main()
