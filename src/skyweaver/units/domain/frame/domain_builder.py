from typing import List

import pandas as pd
from pyproj import CRS
from shapely.geometry import Point

from skyweaver.units.domain.frame.bounds import Bounds
from skyweaver.units.domain.frame.coordinates import ProjectedCoordinate
from skyweaver.units.domain.frame.crs_projection_policies import (
    CRSProjectionPolicy,
    SystemCRS,
)

import geopandas as gpd

from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.domain.frame.local_frame import LocalFrame
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel


class DomainBuilder:

    def __init__(self, projection_policy: CRSProjectionPolicy):
        self.projection_policy = projection_policy

    def build_domain_crs(self, gdf: gpd.GeoDataFrame) -> CRS:

        gdf_copy = gdf.copy()
        gdf_geo = gdf_copy.to_crs(SystemCRS.GEOGRAPHIC)

        initial_guess = gdf_geo.union_all().centroid

        return self.projection_policy.from_origin(initial_guess.y, initial_guess.x)

    def compute_center(self, gdf: gpd.GeoDataFrame) -> ProjectedCoordinate:

        domain_crs = self.build_domain_crs(gdf)

        gdf_metric = gdf.to_crs(domain_crs)
        centroid = gdf_metric.union_all().centroid

        return ProjectedCoordinate(x=centroid.x, y=centroid.y, crs=domain_crs)

    def compute_bounds(self, points: List[Point], padding: float, margin: float):

        xs = [p.x for p in points]
        ys = [p.y for p in points]

        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)

        bounds = Bounds(
            min_x,
            max_x,
            min_y,
            max_y,
        )
        # operational = Bounds(
        #    min_x - padding,
        #    max_x + padding,
        #    min_y - padding,
        #    max_y + padding,
        # )

        # visualization = Bounds(
        #    operational.min_x - margin,
        #    operational.max_x + margin,
        #    operational.min_y - margin,
        #    operational.max_y + margin,
        # )

        return bounds.expand(padding), bounds.expand(margin)  # visualization

    def _from_layers(self, layers: list[gpd.GeoDataFrame]):
        if not layers:
            raise ValueError("At least one spatial layer is required.")

        for layer in layers:
            if layer.crs is None:
                raise ValueError("All layers must have a defined CRS.")

        geographic_layers = [layer.to_crs(SystemCRS.GEOGRAPHIC) for layer in layers]

        combined_geo = gpd.GeoDataFrame(
            pd.concat(geographic_layers, ignore_index=True),
            crs=SystemCRS.GEOGRAPHIC,
        )

        return combined_geo

    def build(self, layers, padding, margin) -> Domain:

        gdf = self._from_layers(layers)
        print(f"Combined GeoDataFrame has {len(gdf)} geometries.")
        center = self.compute_center(gdf)
        print(
            f"Computed domain center at ({center.x}, {center.y}) in CRS {center.crs}."
        )
        gdf_metric = gdf.to_crs(center.crs)
        print("Reprojected GeoDataFrame to domain CRS.")
        local_points = LocalFrame.geo_coord_to_local(
            gdf_metric,
            domain_center=center,
        )

        operational, visualization = self.compute_bounds(local_points, padding, margin)
        print(
            f"Converted geometries to local coordinates. Sample local point: ({local_points[0].x}, {local_points[0].y})"
        )
        # operational = self.compute_bounds_axis_aligned(
        #    local_points,
        #    padding,
        # )
        print(f"Computed operational bounds: {operational}")
        # visualization = self.expand_bounds(
        #    operational,
        #    margin,
        # )
        print(f"Computed visualization bounds: {visualization}")
        return Domain(
            center=center,
            operational_bounds=operational,
            visualization_bounds=visualization,
        )

    def compute_bounds_axis_aligned(
        self, points: list[Point], padding: float
    ) -> Bounds:
        if not points:
            raise ValueError("No points provided.")

        max_abs_x = max(abs(p.x) for p in points)
        max_abs_y = max(abs(p.y) for p in points)

        half_width = max_abs_x + padding
        half_height = max_abs_y + padding

        return Bounds.from_ranges(
            min_x=-half_width,
            max_x=+half_width,
            min_y=-half_height,
            max_y=+half_height,
        )

    def expand_bounds(self, bounds: Bounds, margin: float) -> Bounds:
        return bounds.expand(margin)
