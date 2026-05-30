from typing import List

from skyweaver.units.domain.frame.coordinates import ProjectedCoordinate
import geopandas as gpd
from shapely.geometry import Point


class LocalFrame:

    # def __init__(self, domain_center: ProjectedCoordinate):
    #    self.crs = domain_center.crs
    #    self.origin_x = domain_center.x
    #    self.origin_y = domain_center.y

    @staticmethod
    def geo_coord_to_local(
        gdf: gpd.GeoDataFrame, domain_center: ProjectedCoordinate
    ) -> List[Point]:

        # if gdf.crs != domain_center.crs:
        #    gdf_metric = gdf.to_crs(domain_center.crs)
        # else:
        #    gdf_metric = gdf

        gdf_metric = gdf.to_crs(domain_center.crs)
        pois: List[Point] = []

        for geom in gdf_metric.geometry:

            if not isinstance(geom, Point):
                raise TypeError(
                    f"LocalFrame expects Point geometries. Got {type(geom).__name__}"
                )

            pois.append(
                Point(
                    geom.x - domain_center.x,
                    geom.y - domain_center.y,
                )
            )

        return pois

    # Local frame → Domain CRS
    @staticmethod
    def local_to_geo_coord(
        pois: List[Point], domain_center: ProjectedCoordinate
    ) -> gpd.GeoDataFrame:

        converted_pois = []
        for poi in pois:
            x = poi.x + domain_center.x
            y = poi.y + domain_center.y
            converted_pois.append(Point(x, y))

        gdf = gpd.GeoDataFrame(geometry=converted_pois, crs=domain_center.crs)
        return gdf
