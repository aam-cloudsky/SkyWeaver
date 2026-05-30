from dataclasses import dataclass

from dataclasses import asdict
import json

from geopandas import GeoDataFrame
import geopandas as gpd
from shapely.geometry import LineString


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
        self,
        pallet: dict[type[Parcel], Parcel],
    ) -> SceneSnapshot:

        layers: list[MapLayer] = []

        domain_parcel = pallet.get(DomainParcel)
        grid_parcel = pallet.get(GridParcel)
        heliports_parcel = pallet.get(HeliportsParcel)
        vertiports_parcel = pallet.get(VertiportsParcel)
        routes_parcel = pallet.get(RoutesParcel)

        if not isinstance(domain_parcel, DomainParcel):
            return SceneSnapshot(layers=[])

        domain = domain_parcel.domain

        if isinstance(heliports_parcel, HeliportsParcel):
            layers.append(self._build_heliports_layer(domain, heliports_parcel))

        if isinstance(vertiports_parcel, VertiportsParcel):
            layers.append(self._build_vertiports_layer(domain, vertiports_parcel))

        if isinstance(routes_parcel, RoutesParcel) and isinstance(
            grid_parcel, GridParcel
        ):
            layers.append(
                self._build_routes_layer(domain, grid_parcel.grid, routes_parcel)
            )

        return SceneSnapshot(layers=layers)

    def _build_vertiports_layer(
        self,
        domain: Domain,
        vertiports_parcel: VertiportsParcel,
    ) -> MapLayer:
        vertiports = vertiports_parcel.vertiports
        gdf = domain.local_to_geo_coord(vertiports)

        return MapLayer(
            id="vertiports",
            geometry_type="Point",
            crs=domain.crs.to_string(),
            geodata=gdf,
        )

    def _build_heliports_layer(
        self,
        domain: Domain,
        heliports_parcel: HeliportsParcel,
    ) -> MapLayer:
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
        domain: Domain,
        grid: HexGrid,
        routes_parcel: RoutesParcel,
    ) -> MapLayer:
        rows = []

        for route_index, path in enumerate(routes_parcel.routes_graph.paths):
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
