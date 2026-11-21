from dataclasses import asdict, dataclass
import json

import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import LineString, Point

from skyweaver.model.routes import Routes
from skyweaver.model.sites import Heliports, Vertiports
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid


@dataclass(frozen=True)
class MapLayer:
    id: str
    geometry_type: str
    crs: str
    geodata: GeoDataFrame


@dataclass(frozen=True)
class SceneSnapshot:
    layers: list[MapLayer]


# Transport dataclasses for serialization
@dataclass(frozen=True)
class TransportLayer:
    id: str
    geometry_type: str
    crs: str
    geojson: dict


@dataclass(frozen=True)
class TransportScene:
    layers: list[TransportLayer]


class SceneMaterializer:
    """
    Materializes the values of the flow into GIS-ready scene snapshots.

    Responsibilities:
    - consume the domain, heliports, vertiports, routes and grid values;
    - project internal operational state into geographic representations;
    - transform local continuous coordinates into GIS-compatible layers;
    - build frontend-oriented spatial scene snapshots;
    - encapsulate runtime-to-map translation logic.

    This class represents the GIS materialization boundary between:
        - the internal operational/runtime model;
        - the external spatial visualization model.

    The generated scene is intentionally detached from:
        - hexagonal discretization internals;
        - the Reed session that produced the values;
        - operational units;
        - routing implementation details.

    Pipeline:
        Flow values
            ↓
        Local Continuous Geometry
            ↓
        Geographic Projection
            ↓
        GeoDataFrame Layers
            ↓
        SceneSnapshot

    Coordinate spaces involved:
        Geographic CRS
            ↓
        Domain CRS
            ↓
        Local Continuous Cartesian Space
            ↓
        Hexagonal Discretization

    The materializer reverses the discretization boundary and exposes
    only GIS-consumable geographic layers.

    Notes:
    - Frontend consumers should interact with SceneSnapshot and MapLayer,
      never directly with flow values or hex structures.
    - GeoDataFrames are currently used as the intermediate GIS boundary.
    - Serialization and transport concerns are intentionally external
      to this class.
    """

    def serialize_scene(
        self,
        scene: SceneSnapshot,
    ) -> TransportScene:
        """
        Convert a GIS-rich SceneSnapshot into a transport-safe scene.

        Responsibilities:
        - reproject all layers into EPSG:4326;
        - convert GeoDataFrames into GeoJSON-compatible dictionaries;
        - isolate websocket/frontend transport concerns from the
          runtime GIS materialization layer.

        Notes:
        - SceneSnapshot remains GIS-oriented and GeoDataFrame-based.
        - TransportScene is frontend/websocket oriented.
        - Web GIS frontends are expected to consume WGS84 GeoJSON.
        """

        transport_layers: list[TransportLayer] = []

        for layer in scene.layers:

            gdf_wgs84 = layer.geodata.to_crs("EPSG:4326")

            geojson = json.loads(gdf_wgs84.to_json())

            transport_layers.append(
                TransportLayer(
                    id=layer.id,
                    geometry_type=layer.geometry_type,
                    crs="EPSG:4326",
                    geojson=geojson,
                )
            )

        return TransportScene(layers=transport_layers)

    def serialize_scene_to_dict(
        self,
        scene: SceneSnapshot,
    ) -> dict:

        transport_scene = self.serialize_scene(scene)

        return asdict(transport_scene)

    def materialize_values(
        self,
        domain: Domain,
        heliports: Heliports | None,
        vertiports: Vertiports | None,
        routes: Routes | None,
        grid: HexGrid | None,
    ) -> SceneSnapshot:
        """The heliports, vertiports and routes layers, in this order."""

        layers: list[MapLayer] = []

        if heliports is not None:
            layers.append(self._points_layer("heliports", domain, heliports.points))

        if vertiports is not None:
            layers.append(self._points_layer("vertiports", domain, vertiports.points))

        if routes is not None and grid is not None:
            layers.append(self._build_routes_layer(domain, grid, routes))

        return SceneSnapshot(layers=layers)

    def _points_layer(self, layer_id: str, domain: Domain, points) -> MapLayer:
        return MapLayer(
            id=layer_id,
            geometry_type="Point",
            crs=domain.crs.to_string(),
            geodata=domain.local_to_geo_coord(list(points)),
        )

    def _build_routes_layer(
        self,
        domain: Domain,
        grid: HexGrid,
        routes: Routes,
    ) -> MapLayer:
        rows = []

        for route_index, path in enumerate(routes.routes_graph.paths):
            if len(path) < 2:
                continue

            local_points = [grid.cartesian_cell_center(cell) for cell in path]
            gdf = domain.local_to_geo_coord(local_points)

            coords = [
                (point.x, point.y) for point in gdf.geometry if isinstance(point, Point)
            ]

            if len(coords) < 2:
                continue

            line = LineString(coords)

            rows.append(
                {
                    "route_id": route_index,
                    "num_cells": len(path),
                    "origin_q": path[0].coord.q,
                    "origin_r": path[0].coord.r,
                    "target_q": path[-1].coord.q,
                    "target_r": path[-1].coord.r,
                    "geometry": line,
                }
            )

        if not rows:
            gdf = gpd.GeoDataFrame(
                geometry=[],
                crs=domain.crs,
            )
        else:
            gdf = gpd.GeoDataFrame(
                rows,
                geometry="geometry",
                crs=domain.crs,
            )

        return MapLayer(
            id="routes",
            geometry_type="LineString",
            crs=domain.crs.to_string(),
            geodata=gdf,
        )


def materialize_scene(
    domain: Domain,
    heliports: Heliports,
    vertiports: Vertiports,
    routes: Routes,
    grid: HexGrid,
) -> SceneSnapshot:
    """The scene the frontend draws: heliports, vertiports and routes layers."""

    return SceneMaterializer().materialize_values(
        domain=domain,
        heliports=heliports,
        vertiports=vertiports,
        routes=routes,
        grid=grid,
    )
