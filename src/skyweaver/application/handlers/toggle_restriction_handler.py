from shapely.geometry import Point
import geopandas as gpd

from skyweaver.application.intents.toggle_restriction import (
    ToggleRestriction,
)
from skyweaver.application.runtime.application_context import (
    ApplicationContext,
)


class ToggleRestrictionHandler:
    """
    Toggle traversability restrictions from frontend GIS interactions.
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def __call__(self, intent: ToggleRestriction) -> None:

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

        heliports = self.context.units.alignment._outpost.heliports_parcel.heliports

        heliport_cells = set(grid.get_cell_from_cartesians(heliports))

        if cell in heliport_cells:
            return

        vertiports = self.context.units.routes._outpost.vertiports_parcel.vertiports

        vertiport_cells = set(grid.get_cell_from_cartesians(vertiports))

        if cell in vertiport_cells:
            return

        if cell.is_traversable:
            cell.set_restricted()
        else:
            cell.set_available()

        self.context.units.routes.run()
