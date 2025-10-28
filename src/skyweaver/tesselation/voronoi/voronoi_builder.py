# src/skyweaver/scenarios/components/tesselation/voronoi_builder.py
from __future__ import annotations
from typing import List, Optional, Tuple
import numpy as np
import plotly.graph_objects as go
from shapely.geometry import Point, Polygon, MultiPolygon, GeometryCollection
from scipy.spatial import Voronoi
import networkx as nx

from skyweaver.tesselation.voronoi.voronoi_cell import VoronoiCell


class VoronoiBuilder:
    """
    Wrapper around scipy.spatial.Voronoi to build bounded Voronoi polygons
    and convert them into VoronoiCell instances.

    Automatically adds virtual "border" points around the domain to ensure
    all interior seeds generate bounded cells.
    """

    # -------------------------------------------------------------
    @staticmethod
    def _normalize_geometry(clipped) -> Optional[Polygon]:
        """Return a valid Polygon if possible, or None otherwise."""
        if clipped.is_empty:
            return None
        if isinstance(clipped, Polygon):
            return clipped
        if isinstance(clipped, MultiPolygon):
            return max(clipped.geoms, key=lambda g: g.area)
        if isinstance(clipped, GeometryCollection):
            polys = [g for g in clipped.geoms if isinstance(g, Polygon)]
            if not polys:
                return None
            return max(polys, key=lambda g: g.area)
        return None

    # -------------------------------------------------------------
    @staticmethod
    def _generate_border_points(bounds: tuple[tuple[float, float], tuple[float, float]], padding: float = 50.0) -> List[Point]:
        """Generate auxiliary border points around the domain to bound the Voronoi diagram."""
        (min_x, max_x), (min_y, max_y) = bounds
        cx, cy = (min_x + max_x) / 2, (min_y + max_y) / 2

        return [
            Point(min_x - padding, min_y - padding),
            Point(max_x + padding, min_y - padding),
            Point(max_x + padding, max_y + padding),
            Point(min_x - padding, max_y + padding),
            Point(cx, min_y - padding),
            Point(cx, max_y + padding),
            Point(min_x - padding, cy),
            Point(max_x + padding, cy),
        ]

    # -------------------------------------------------------------
    @staticmethod
    def build(bounds: tuple[tuple[float, float], tuple[float, float]], seed_points: List[Point]) -> Tuple[List[VoronoiCell], nx.Graph, Voronoi]:
        """Construct Voronoi cells clipped to the domain bounds."""
        if len(seed_points) < 2:
            raise ValueError(
                "At least two seed points are required to build a Voronoi diagram."
            )

        # --- Add auxiliary border points (not returned as cells) ---
        border_points = VoronoiBuilder._generate_border_points(
            bounds, padding=100.0)
        all_points = seed_points + border_points

        pts = np.array([[p.x, p.y] for p in all_points])
        vor = Voronoi(pts)

        cells = VoronoiBuilder.cells_from_voronoi(
            vor, seed_points, bounds, num_real=len(seed_points)
        )

        graph = VoronoiBuilder.graph_from_voronoi(
            vor, seed_points, num_real=len(seed_points)
        )

        return cells, graph, vor
    
    @staticmethod
    def cells_from_voronoi(vor: Voronoi, seed_points: list[Point], bounds: tuple[tuple[float, float], tuple[float, float]], num_real: int) -> List[VoronoiCell]:
        """Convert scipy Voronoi object into VoronoiCell instances."""
        min_x, max_x = bounds[0]
        min_y, max_y = bounds[1]
        bbox = Polygon([
            (min_x, min_y), (max_x, min_y),
            (max_x, max_y), (min_x, max_y)
        ])

        cells: List[VoronoiCell] = []

        for i, region_index in enumerate(vor.point_region):
            if i >= num_real:
                # skip dummy border points
                continue

            region = vor.regions[region_index]
            if -1 in region or not region:
                continue  # Skip unbounded or empty regions

            raw_polygon = Polygon(vor.vertices[region])
            clipped = raw_polygon.intersection(bbox)
            polygon = VoronoiBuilder._normalize_geometry(clipped)

            if polygon is None:
                continue

            x, y = map(list, polygon.exterior.xy)
            vertices = [Point(px, py) for px, py in zip(x, y)]

            cells.append(VoronoiCell(
                seed_point=seed_points[i],
                polygon=polygon,
                vertices=vertices,
            ))

        return cells

    @staticmethod
    def graph_from_voronoi(vor: Voronoi, seed_points: list[Point], num_real: int) -> nx.Graph:
        """
        Build an adjacency graph from scipy Voronoi object.
        - Each node represents a real seed (not a border one)
        - Edges connect neighboring cells (ridge_points)
        """
        G = nx.Graph()

        # --- Add nodes for all real seeds ---
        for i, p in enumerate(seed_points[:num_real]):
            G.add_node(i, pos=(p.x, p.y))

        # --- Add edges for ridge-connected seeds ---
        for i, j in vor.ridge_points:
            if i < num_real and j < num_real:  # exclude border padding
                p1, p2 = seed_points[i], seed_points[j]
                distance = np.hypot(p1.x - p2.x, p1.y - p2.y)
                G.add_edge(i, j, weight=distance)

        return G


# ==============================================================
# Stand-alone interactive test (Plotly)
# ==============================================================
if __name__ == "__main__":
    rng = np.random.default_rng(42)
    bounds = ((-100, 100), (-100, 100))
    seed_points = [Point(*rng.uniform(-90, 90, 2)) for _ in range(15)]

    cells, graph, vor = VoronoiBuilder.build(bounds, seed_points)

    print(f"[INFO] Generated {len(cells)} Voronoi cells (all bounded).")
    print(
        f"[INFO] Graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")

    fig = go.Figure()

    # --- Cells ---
    for i, cell in enumerate(cells):
        x, y = map(list, cell.polygon.exterior.xy)
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            fill="toself",
            fillcolor=f"rgba({rng.integers(0, 255)}, {rng.integers(0, 255)}, {rng.integers(0, 255)}, 0.3)",
            line=dict(color="black", width=1),
            hoverinfo="text",
            name=f"Cell {i}",
            text=f"Cell {i}<br>Seed: ({cell.seed_point.x:.2f}, {cell.seed_point.y:.2f})"
        ))

    # --- Graph edges ---
    for u, v in graph.edges:
        x0, y0 = graph.nodes[u]["pos"]
        x1, y1 = graph.nodes[v]["pos"]
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1],
                                 mode="lines", line=dict(color="gray", width=1),
                                 hoverinfo="none", showlegend=False))

    # --- Seeds ---
    fig.add_trace(go.Scatter(
        x=[p.x for p in seed_points],
        y=[p.y for p in seed_points],
        mode="markers+text",
        marker=dict(color="red", size=8, line=dict(color="black", width=1)),
        text=[f"S{i}" for i in range(len(seed_points))],
        textposition="top center",
        name="Seeds"
    ))

    fig.update_layout(
        title="Voronoi Diagram (Bounded) with Adjacency Graph",
        xaxis=dict(scaleanchor="y", showgrid=True, zeroline=False),
        yaxis=dict(showgrid=True, zeroline=False),
        width=800, height=800, template="plotly_white"
    )
    fig.show()
