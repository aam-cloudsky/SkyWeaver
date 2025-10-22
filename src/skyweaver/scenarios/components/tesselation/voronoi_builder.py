from typing import List

from shapely import Point


from skyweaver.scenarios.components.voronoi.voronoi_cell import VoronoiCell


class VoronoiBuilder:
    def build(self, seed_points: List[Point]) -> List[VoronoiCell]:
        """Generate Voronoi cells from given seed points."""
        from scipy.spatial import Voronoi
        import shapely.geometry as geom

        coords = [(p.x, p.y) for p in seed_points]
        vor = Voronoi(coords)

        cells = []
        for i, region_idx in enumerate(vor.point_region):
            region = vor.regions[region_idx]
            if not region or -1 in region:
                continue
            polygon = geom.Polygon(vor.vertices[region])
            cell = VoronoiCell(
                id=f"cell_{i}",
                seed_point=seed_points[i],
                polygon=polygon,
                vertices=[Point(*v) for v in polygon.exterior.coords],
            )
            cell.update_validity()
            cells.append(cell)
        return cells
