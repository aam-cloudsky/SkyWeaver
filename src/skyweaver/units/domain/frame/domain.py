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
        self._center = center
        self._operational_bounds = operational_bounds
        self._visualization_bounds = visualization_bounds

        self._local_frame = LocalFrame(center)

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

    def project_to_domain(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        return gdf.to_crs(self.crs)

    def to_local(self, gdf: gpd.GeoDataFrame) -> list[Point]:
        gdf_metric = self.project_to_domain(gdf)
        return self._local_frame.to_local(gdf_metric)

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
