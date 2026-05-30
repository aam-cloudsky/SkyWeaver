from shapely.geometry import Point

from skyweaver.application.intents.add_vertiport import AddVertiport
from skyweaver.application.runtime.application_context import ApplicationContext


class AddVertiportHandler:
    """
    Handle frontend-driven vertiport insertion requests.

    Responsibilities:
    - receive geographic WGS84 coordinates from the application intent layer;
    - project frontend geographic coordinates into the operational domain space;
    - discretize projected coordinates into hexagonal operational cells;
    - validate conflicts against existing heliports and vertiports;
    - trigger route recomputation after successful insertion.

    Spatial pipeline:
        Frontend WGS84 Coordinates
                ↓
        Domain Projection
                ↓
        Local Cartesian Space
                ↓
        Hexagonal Discretization
                ↓
        Operational Routing Graph
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def __call__(self, intent: AddVertiport) -> None:

        domain = self.context.runtime.units.domain._outpost.domain_parcel.domain

        grid = self.context.runtime.units.grid._outpost.grid_parcel.grid

        geo_point = Point(intent.longitude, intent.latitude)

        import geopandas as gpd

        geo_gdf = gpd.GeoDataFrame(
            geometry=[geo_point],
            crs="EPSG:4326",
        )

        local_point = domain.to_local(geo_gdf)[0]

        cell = grid.get_cell_from_cartesian(local_point)

        if cell is None:
            return

        heliports = (
            self.context.runtime.units.alignment._outpost.heliports_parcel.heliports
        )
        heliport_cells = set(grid.get_cell_from_cartesians(heliports))

        if cell in heliport_cells:
            return

        vertiports = (
            self.context.runtime.units.routes._outpost.vertiports_parcel.vertiports
        )
        vertiport_cells = set(grid.get_cell_from_cartesians(vertiports))

        if cell in vertiport_cells:
            return

        self.context.runtime.units.routes.add_vertiport(cell)

        self.context.runtime.units.routes.run()
