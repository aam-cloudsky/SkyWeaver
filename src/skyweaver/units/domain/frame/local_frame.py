from typing import List

from skyweaver.units.domain.frame.coordinates import ProjectedCoordinate
import geopandas as gpd
from shapely.geometry import Point


class LocalFrame:

    def __init__(self, domain_center: ProjectedCoordinate):
        self.crs = domain_center.crs
        self.origin_x = domain_center.x
        self.origin_y = domain_center.y

    def to_local(self, gdf: gpd.GeoDataFrame) -> List[Point]:

        if gdf.crs != self.crs:
            gdf_metric = gdf.to_crs(self.crs)
        else:
            gdf_metric = gdf

        pois: List[Point] = []

        for geom in gdf_metric.geometry:

            if not isinstance(geom, Point):
                raise TypeError(
                    f"LocalFrame expects Point geometries. Got {type(geom).__name__}"
                )

            pois.append(
                Point(
                    geom.x - self.origin_x,
                    geom.y - self.origin_y,
                )
            )

        return pois

    # Local frame → Domain CRS
    def to_crs(self, pois: List[Point]) -> gpd.GeoDataFrame:

        converted_pois = []
        for poi in pois:
            x = poi.x + self.origin_x
            y = poi.y + self.origin_y
            converted_pois.append(Point(x, y))

        gdf = gpd.GeoDataFrame(geometry=converted_pois, crs=self.crs)
        return gdf
