from dataclasses import dataclass
from typing import Literal, Optional

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon

from skyweaver.core.logistics.depot import Depot
from skyweaver.grid.structure.hexgrid import HexGrid
from skyweaver.grid.geometry.hexcell import HexCell
from skyweaver.grid.geometry.hexcoord import HexCoord


# ============================================================
# IHM Event Model (ONLY what UI emits)
# ============================================================

MouseButton = Literal["left", "middle", "right"]
MouseEventType = Literal["press", "release"]


@dataclass(frozen=True)
class HexMouseEvent:
    coord: HexCoord
    event_type: MouseEventType
    button: MouseButton
    x: float
    y: float


def _button_name(button: int) -> MouseButton:
    if button == 1:
        return "left"
    elif button == 2:
        return "middle"
    elif button == 3:
        return "right"
    else:
        raise ValueError(f"Unknown mouse button: {button}")


# ============================================================
# Matplotlib HexGrid IHM
# ============================================================

class MatplotlibHexGridIHM:
    """
    Pure UI layer.

    Responsibilities:
    - Draw HexGrid
    - Convert mouse (x, y) → HexCell
    - Emit mouse intentions (press / release)

    Non-responsibilities:
    - No mutation
    - No validation
    - No business rules
    """

    def __init__(self, grid: HexGrid):
        self.grid = grid

        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.set_aspect("equal")

        self._draw_grid()
        self._configure_axes()
        self._connect_events()

    # --------------------------------------------------------
    # Rendering
    # --------------------------------------------------------

    def _draw_grid(self):
        for cell in self.grid.iter_domain_cells():
            self._draw_cell(cell)

    def _draw_cell(self, cell: HexCell):
        poly = cell.polygon.exterior.coords
        face = "lightcoral" if not cell.available else "none"

        patch = MplPolygon(
            poly,
            closed=True,
            edgecolor="gray",
            facecolor=face,
            linewidth=0.8,
            zorder=1,
        )

        self.ax.add_patch(patch)

    def _configure_axes(self):
        (xmin, xmax), (ymin, ymax) = self.grid.get_domain()

        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(ymin, ymax)
        self.ax.set_title("HexGrid IHM (Matplotlib)")
        self.ax.grid(False)

    # --------------------------------------------------------
    # Event wiring
    # --------------------------------------------------------

    def _connect_events(self):
        self.fig.canvas.mpl_connect(
            "button_press_event",
            self._on_mouse_press
        )
        self.fig.canvas.mpl_connect(
            "button_release_event",
            self._on_mouse_release
        )

    # --------------------------------------------------------
    # Event handlers
    # --------------------------------------------------------

    def _on_mouse_press(self, event):
        self._handle_mouse_event(event, event_type="press")

    def _on_mouse_release(self, event):
        self._handle_mouse_event(event, event_type="release")

    def _handle_mouse_event(self, event, event_type: MouseEventType):
        if event.inaxes != self.ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        cell = self.grid.get_cell_from_cartesian(event.xdata, event.ydata)
        if cell is None:
            return

        evt = HexMouseEvent(
            coord=cell.coord,
            event_type=event_type,
            button=_button_name(event.button),
            x=event.xdata,
            y=event.ydata,
        )

        self.on_hex_event(evt)

    # --------------------------------------------------------
    # Output hook (Application Layer consumes this)
    # --------------------------------------------------------

    def on_hex_event(self, event: HexMouseEvent):
        """
        Override or inject.

        This is the ONLY output of the UI.
        """
        print(
            f"[IHM] {event.event_type.upper():7} | "
            f"button={event.button:6} | "
            f"hex={event.coord} | "
            f"x={event.x:.1f}, y={event.y:.1f}"
        )

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------

    def show(self):
        plt.show()


# ============================================================
# Example usage (DEBUG / EXAMPLE ONLY)
# ============================================================

def main():
    Depot()  # ensure Depot exists

    grid = HexGrid(cell_size=100.0)
    ihm = MatplotlibHexGridIHM(grid)

    ihm.show()


if __name__ == "__main__":
    main()
