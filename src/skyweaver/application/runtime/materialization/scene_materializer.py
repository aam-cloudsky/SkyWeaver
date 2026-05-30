from dataclasses import dataclass

from dataclasses import asdict
import json

from geopandas import GeoDataFrame
import geopandas as gpd
from shapely.geometry import LineString


from skyweaver.application.runtime.logistics.runtime_outpost import RuntimeOutpost
from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.geodata_domain_alignment.logistics.vertiports_parcel import (
    VertiportsParcel,
)
from skyweaver.units.geodata_domain_alignment.logistics.heliports_parcel import (
    HeliportsParcel,
)
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
from skyweaver.units.routes.logistics.routes_parcel import RoutesParcel
from skyweaver.units.hexgrid.logistics.grid_parcel import GridParcel
from shapely.geometry import Point


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
    Materializes runtime synchronization state into GIS-ready scene snapshots.

    Responsibilities:
    - consume synchronized runtime parcels;
    - project internal operational state into geographic representations;
    - transform local continuous coordinates into GIS-compatible layers;
    - build frontend-oriented spatial scene snapshots;
    - encapsulate runtime-to-map translation logic.

    This class represents the GIS materialization boundary between:
        - the internal operational/runtime model;
        - the external spatial visualization model.

    The generated scene is intentionally detached from:
        - hexagonal discretization internals;
        - parcel synchronization semantics;
        - operational units;
        - routing implementation details.

    Pipeline:
        Runtime Parcels
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
      never directly with parcels or hex structures.
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

    def materialize(
        self, pallet: dict[type[Parcel], Parcel], outpost: RuntimeOutpost
    ) -> SceneSnapshot:

        layers: list[MapLayer] = []

        for parcel_type, parcel in pallet.items():
            if isinstance(parcel, HeliportsParcel):
                layers.append(self._build_heliports_layer(parcel, outpost))

            if isinstance(parcel, VertiportsParcel):
                layers.append(self._build_vertiports_layer(parcel, outpost))

            if isinstance(parcel, RoutesParcel):
                print(parcel)
                layers.append(self._build_routes_layer(parcel, outpost))

        return SceneSnapshot(layers=layers)

    def _build_vertiports_layer(
        self, vertiports_parcel: VertiportsParcel, outpost: RuntimeOutpost
    ) -> MapLayer:
        snapped_points = []
        grid = outpost.grid_parcel.grid
        domain = outpost.domain_parcel.domain

        for point in vertiports_parcel.vertiports:
            cell = grid.get_cell_from_cartesian(point)
            if cell is None:
                continue

            snapped_points.append(grid.cartesian_cell_center(cell))

        gdf = domain.local_to_geo_coord(snapped_points)

        return MapLayer(
            id="vertiports",
            geometry_type="Point",
            crs=domain.crs.to_string(),
            geodata=gdf,
        )

    def _build_heliports_layer(
        self,
        heliports_parcel: HeliportsParcel,
        runtime_outpost: RuntimeOutpost,
    ) -> MapLayer:
        domain = runtime_outpost.domain_parcel.domain
        heliports = heliports_parcel.heliports
        gdf = domain.local_to_geo_coord(heliports)

        return MapLayer(
            id="heliports",
            geometry_type="Point",
            crs=domain.crs.to_string(),
            geodata=gdf,
        )

    def _build_routes_layer(
        self,
        routes_parcel: RoutesParcel,
        runtime_outpost: RuntimeOutpost,
    ) -> MapLayer:
        rows = []

        domain = runtime_outpost.domain_parcel.domain
        grid = runtime_outpost.grid_parcel.grid
        print(
            f"[SceneMaterializer] incoming route paths: {len(routes_parcel.routes_graph.paths)}"
        )

        for route_index, path in enumerate(routes_parcel.routes_graph.paths):
            print(f"[SceneMaterializer] path {route_index} cell count: {len(path)}")

            if len(path) < 2:
                continue

            local_points = [grid.cartesian_cell_center(cell) for cell in path]
            gdf = domain.local_to_geo_coord(local_points)

            coords = [
                (point.x, point.y) for point in gdf.geometry if isinstance(point, Point)
            ]

            print(
                f"[SceneMaterializer] path {route_index} projected coords: {len(coords)}"
            )

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
