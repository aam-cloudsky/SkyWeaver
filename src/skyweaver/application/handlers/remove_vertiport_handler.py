from shapely.geometry import Point
import geopandas as gpd

from skyweaver.application.intents.remove_vertiport import (
    RemoveVertiport,
)
from skyweaver.application.runtime.application_context import (
    ApplicationContext,
)


class RemoveVertiportHandler:
    """
    Remove an operational vertiport from frontend GIS interactions.

    Responsibilities:
    - receive WGS84 geographic coordinates from the application layer;
    - project frontend coordinates into the operational local frame;
    - discretize local coordinates into operational hexagonal cells;
    - remove existing vertiports from the routing system;
    - trigger route recomputation after topology mutations.

    Spatial pipeline:
        Frontend WGS84 Coordinates
                ↓
        Domain Projection
                ↓
        Local Cartesian Space
                ↓
        Hexagonal Cell Projection
                ↓
        Vertiport Removal
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def __call__(self, intent: RemoveVertiport) -> None:

        domain = self.context.units.domain._outpost.domain_parcel.domain

        grid = self.context.units.grid._outpost.grid_parcel.grid

        geo_point = Point(intent.longitude, intent.latitude)

        geo_gdf = gpd.GeoDataFrame(
            geometry=[geo_point],
            crs="EPSG:4326",
        )

        local_point = domain.to_local(geo_gdf)[0]

        cell = grid.get_cell_from_cartesian(local_point)

        if cell is None:
            return

        vertiports = self.context.units.routes._outpost.vertiports_parcel.vertiports

        vertiport_cells = set(grid.get_cell_from_cartesians(vertiports))

        if cell not in vertiport_cells:
            return

        self.context.units.routes.remove_vertiport(cell)

        self.context.units.routes.run()
