from __future__ import annotations
import plotly.graph_objects as go
import plotly.io as pio
from shapely.geometry import Point
from skyweaver.airspace.airspace_state import AirspaceState
from skyweaver.core.enums.zone_type import ZoneType
from typing import Dict, List
import numpy as np


class AirspaceViewer:
    """Layer-based reactive Plotly viewer for SkyWeaver airspace."""

    def __init__(self) -> None:
        self.state: AirspaceState = AirspaceState()
        self.figure: go.Figure = go.Figure()  # ✅ explicitly typed
        self._layers: Dict[str, List[int]] = {}

        self._setup_layout()
        self._draw_domain()
        self.refresh_all(dynamic_only=True)
        self._register_callbacks()
        self.show()

    # --------------------------------------------------------------
    # Layout and callbacks
    # --------------------------------------------------------------
    def _setup_layout(self) -> None:
        self.figure.update_layout(
            title="SkyWeaver Airspace",
            xaxis=dict(scaleanchor="y", showgrid=True, zeroline=False),
            yaxis=dict(showgrid=True, zeroline=False),
            width=800,
            height=800,
            template="plotly_white",
            legend=dict(x=0.02, y=0.98),
        )

        (xmin, xmax), (ymin, ymax) = self.state.domain
        self.figure.update_xaxes(range=[xmin, xmax])
        self.figure.update_yaxes(range=[ymin, ymax])

    def _register_callbacks(self) -> None:
        self.state.add_callback(
            "uav_points", lambda *_: self.refresh_layer("distribution"))
        self.state.add_callback(
            "mav_points", lambda *_: self.refresh_layer("distribution"))
        self.state.add_callback(
            "clusters", lambda *_: self.refresh_layer("clusters"))
        self.state.add_callback(
            "voronoi_cells", lambda *_: self.refresh_layer("voronoi"))

    # --------------------------------------------------------------
    # Drawing helpers
    # --------------------------------------------------------------
    def _record_traces(self, name: str, start_idx: int) -> None:
        end_idx = len(self.figure.data or ())  # type: ignore
        self._layers[name] = list(range(start_idx, end_idx))

    def _clear_layer(self, name: str) -> None:
        if name not in self._layers:
            return
        keep = [i for i in range(len(self.figure.data or ()))  # type: ignore
                if i not in self._layers[name]]
        self.figure.data = tuple(self.figure.data[i] for i in keep)
        self._layers[name] = []

    # --------------------------------------------------------------
    # Core drawing
    # --------------------------------------------------------------
    def _draw_domain(self) -> None:
        s = self.state
        (xmin, xmax), (ymin, ymax) = s.domain
        print(f"[DEBUG] Drawing domain: X=({xmin},{xmax}), Y=({ymin},{ymax})")

        start_idx = len(self.figure.data or ())  # type: ignore
        x_box = [xmin, xmax, xmax, xmin, xmin]
        y_box = [ymin, ymin, ymax, ymax, ymin]

        self.figure.add_scatter(
            x=x_box,
            y=y_box,
            mode="lines",
            line=dict(color="black", width=2, dash="dot"),
            name="Domain Boundary",
            hoverinfo="skip",
        )
        self.figure.add_scatter(
            x=[(xmin + xmax) / 2],
            y=[(ymin + ymax) / 2],
            mode="text",
            text=["EMPTY AIRSPACE"],
            textfont=dict(size=16, color="gray"),
            textposition="middle center",
            name="Label",
            showlegend=False,
        )
        self._record_traces("domain", start_idx)

    def _draw_distribution(self) -> None:
        s = self.state
        start_idx = len(self.figure.data or ())  # type: ignore

        if s.uav_points:
            self.figure.add_scatter(
                x=[p.x for p in s.uav_points],
                y=[p.y for p in s.uav_points],
                mode="markers",
                marker=dict(color="blue", size=6,
                            line=dict(width=1, color="black")),
                name="UAV Points",
            )

        if s.mav_points:
            self.figure.add_scatter(
                x=[p.x for p in s.mav_points],
                y=[p.y for p in s.mav_points],
                mode="markers",
                marker=dict(color="red", size=6, line=dict(
                    width=1, color="black")),
                name="MAV Points",
            )

        self._record_traces("distribution", start_idx)

    def _draw_clusters(self) -> None:
        s = self.state
        start_idx = len(self.figure.data or ())  # type: ignore
        for cluster in s.clusters:
            if hasattr(cluster, "polygon"):
                color = "green" if cluster.zone_type == ZoneType.UAV else "red"
                x, y = cluster.polygon.exterior.xy
                self.figure.add_scatter(
                    x=list(x),
                    y=list(y),
                    mode="lines",
                    fill="toself",
                    fillcolor="rgba(0,150,0,0.2)" if color == "green" else "rgba(200,0,0,0.2)",
                    line=dict(color=color, width=1),
                    name=f"Cluster ({color.upper()})",
                )
        self._record_traces("clusters", start_idx)

    def _draw_voronoi(self) -> None:
        s = self.state
        start_idx = len(self.figure.data or ()) #type: ignore
        for cell in s.voronoi_cells:
            x, y = cell.polygon.exterior.xy
            self.figure.add_scatter(
                x=list(x),
                y=list(y),
                mode="lines",
                fill="toself",
                fillcolor="rgba(0,0,255,0.1)",
                line=dict(color="black", width=1),
                name="Voronoi Cell",
                hoverinfo="skip",
            )
        self._record_traces("voronoi", start_idx)

    # --------------------------------------------------------------
    # Refresh and show
    # --------------------------------------------------------------
    def refresh_layer(self, name: str) -> None:
        self._clear_layer(name)
        if name == "distribution":
            self._draw_distribution()
        elif name == "clusters":
            self._draw_clusters()
        elif name == "voronoi":
            self._draw_voronoi()

    def refresh_all(self, dynamic_only: bool = False) -> None:
        if not dynamic_only:
            self.figure.data = ()
            self._layers.clear()
            self._draw_domain()
        self._draw_voronoi()
        self._draw_clusters()
        self._draw_distribution()

    def show(self) -> None:
        pio.renderers.default = "browser"
        self.figure.show()


# --------------------------------------------------------------
# Manual test
# --------------------------------------------------------------
if __name__ == "__main__":
    print("[INFO] Launching AirspaceViewer standalone test...")
    pio.renderers.default = "browser"
    viewer = AirspaceViewer()
    print("[INFO] AirspaceViewer created successfully.")
