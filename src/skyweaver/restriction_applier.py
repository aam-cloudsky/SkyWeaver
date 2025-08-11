# skyweaver/restriction_applier.py

import geopandas as gpd
from shapely.geometry import Point
from skyweaver.managers.geo_json_manager import GeoJSONManager
from skyweaver.paths import prepare_data_path, change_to_project_root

RESTRICTION_RADIUS_METERS = 3704  # 2 milhas náuticas


def apply_heliport_restrictions_to_grid(grid_path, heliport_path, output_path):
    manager = GeoJSONManager()
    grid = manager.read_geojson(grid_path)
    heliports = manager.read_geojson(heliport_path)

    if grid is None or heliports is None:
        print("❌ Arquivos não foram carregados corretamente.")
        return

    # Garante que heliports está no mesmo CRS do grid
    if heliports.crs is None:
        # define explicitamente se necessário
        heliports.set_crs(epsg=4326, inplace=True)

    # Passo 1: reprojetar para métrico só para o buffer
    metric_crs = 31983
    heliports_metric = heliports.to_crs(epsg=metric_crs)
    heliports_metric["geometry"] = heliports_metric.geometry.buffer(
        RESTRICTION_RADIUS_METERS)

    # Passo 2: voltar ao CRS do grid
    heliport_buffers = heliports_metric.to_crs(grid.crs)

    # Passo 3: calcular interseções
    restricted = grid[grid.intersects(heliport_buffers.unary_union)].copy()
    grid["restricted"] = grid.index.isin(restricted.index)

    manager.write_geojson(grid, output_path)
    print(f"✅ Grid com zonas restritas salvo em: {output_path}")


if __name__ == "__main__":
    change_to_project_root()
    grid_path = prepare_data_path("grids", "grid_rio_niteroi.geojson")
    heliport_path = prepare_data_path("geojson", "heliport.geojson")
    output_path = prepare_data_path(
        "grids", "grid_rio_niteroi_restrito.geojson")

    apply_heliport_restrictions_to_grid(grid_path, heliport_path, output_path)
