from shapely import Point

from skyweaver.units.domain.frame.bounds import Bounds
from skyweaver.units.domain.frame.coordinates import ProjectedCoordinate

import geopandas as gpd

from skyweaver.units.domain.frame.local_frame import LocalFrame


class Domain:

    def __init__(
        self,
        center: ProjectedCoordinate,
        operational_bounds: Bounds,
        visualization_bounds: Bounds,
    ):
        self._center: ProjectedCoordinate = center
        self._operational_bounds: Bounds = operational_bounds
        self._visualization_bounds: Bounds = visualization_bounds

        # self._local_frame = LocalFrame(center)

    @property
    def center(self) -> ProjectedCoordinate:
        return self._center

    @property
    def operational_bounds(self) -> Bounds:
        return self._operational_bounds

    @property
    def visualization_bounds(self) -> Bounds:
        return self._visualization_bounds

    @property
    def crs(self):
        return self._center.crs

    def reproject_to_domain_crs(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        return gdf.to_crs(self.crs)

    def to_local(self, gdf: gpd.GeoDataFrame) -> list[Point]:
        """
        Convert geographic coordinates into the domain-local continuous frame. This transformation projects geometries from an external CRS into the domain CRS and then expresses them relative to the domain-centered local frame.
        The resulting coordinates are still continuous cartesian coordinates.
        They are NOT discretized hexagonal coordinates.
        This local continuous space is later used by the hexagonal grid system to perform:
        - hex cell projection;
        - neighborhood operations;
        - routing;
        - spatial discretization.
        Coordinate spaces involved:
            Geographic CRS
                ↓
            Domain CRS
                ↓
            Local continuous cartesian frame
        """

        return LocalFrame.geo_coord_to_local(gdf, domain_center=self.center)

    def local_to_geo_coord(self, points_local: list[Point]) -> gpd.GeoDataFrame:
        """
        Convert local continuous cartesian coordinates back into geographic space.
        The input coordinates are assumed to belong to the domain-local
        continuous frame centered around the operational domain origin.
        This operation reverses the local-frame transformation and returns
        geometries expressed in the domain CRS.
        """

        return LocalFrame.local_to_geo_coord(points_local, self.center)

    def contains_local_point(self, point: Point) -> bool:
        b = self._operational_bounds
        return b.min_x <= point.x <= b.max_x and b.min_y <= point.y <= b.max_y

    @classmethod
    def null(cls) -> "Domain":
        center = ProjectedCoordinate.default()
        bounds = Bounds.empty()
        return cls(
            center=center, operational_bounds=bounds, visualization_bounds=bounds
        )
