# skyweaver/grid_generator.py

import geopandas as gpd
from shapely.geometry import box
import numpy as np
from skyweaver.geo_json_manager import GeoJSONManager
from skyweaver.paths import change_to_project_root, prepare_data_path


def generate_grid_over_polygon(
    geojson_input_path,
    output_path,
    cell_size=500,
    crs_meters=31983
):
    """
    Gera um grid quadrado sobre um polígono dado, salvando como GeoJSON.
    Usa interseção espacial para recortar apenas as células relevantes.

    Parâmetros:
    - geojson_input_path: str – Caminho para o arquivo GeoJSON do polígono.
    - output_path: str – Caminho para salvar o grid gerado.
    - cell_size: float – Tamanho da célula em metros.
    - crs_meters: int – Código EPSG para projeção métrica (default: 31983 – UTM zona 23S - Brasil).
    Os dados padrão do IBGE são CRS: EPSG:4674, porém não usa UTM, assim as coordenadas estão em graus.
    Já o CRS 31983 é uma projeção UTM que usa metros, o que é mais adequado para cálculos espaciais precisos.
    TODO: Verficar o CRS de cada GeoJSON e transformar tudo para EPSG 31983.
    """
    manager = GeoJSONManager()
    gdf = manager.read_geojson(geojson_input_path)
    if gdf is None:
        print("❌ Não foi possível ler o GeoJSON de entrada.")
        return

    if gdf.crs is None:
        raise ValueError("GeoJSON sem CRS definido.")

    # Reprojeta para sistema métrico, se necessário
    gdf_metric = gdf.to_crs(epsg=crs_meters)

    minx, miny, maxx, maxy = gdf_metric.total_bounds

    x_coords = np.arange(minx, maxx, cell_size)
    y_coords = np.arange(miny, maxy, cell_size)

    grid_cells = []
    for x in x_coords:
        for y in y_coords:
            square = box(float(x), float(y), float(x + cell_size), float(y + cell_size))
            grid_cells.append(square)

    grid = gpd.GeoDataFrame(geometry=grid_cells, crs=f"EPSG:{crs_meters}")
    clipped = grid[grid.intersects(gdf_metric.unary_union)].copy()

    # Adiciona ID sequencial
    clipped["cell_id"] = np.arange(len(clipped))

    # (Opcional) Adicione atributos extras aqui: água, zona restrita, etc

    # Retorna ao CRS original se necessário
    clipped = clipped.to_crs(gdf.crs)

    manager.write_geojson(clipped, output_path)
    print(f"✅ Grid gerado e salvo em: {output_path}")


if __name__ == "__main__":
    change_to_project_root()
    input_path = prepare_data_path("municipios_rj", "rio_niteroi.geojson")
    output_path = prepare_data_path("grids", "grid_rio_niteroi.geojson")

    generate_grid_over_polygon(input_path, output_path, cell_size=500)
