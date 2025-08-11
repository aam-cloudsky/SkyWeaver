import geopandas as gpd
from skyweaver.managers.geo_json_manager import GeoJSONManager
from skyweaver.paths import (
    change_to_project_root,
    get_ibge_malha_path,
    prepare_data_path
)


def export_municipios_union(municipios: list[str], output_filename: str, export_individuais: bool = True):
    """
    Exporta a união de múltiplos municípios em um arquivo GeoJSON com nome arbitrário.
    Também pode exportar arquivos individuais de cada município.

    :param municipios: Lista de nomes de municípios (ex.: ["Rio de Janeiro", "Niterói"])
    :param output_filename: Nome do arquivo final de união (ex.: "rio_niteroi.geojson")
    :param export_individuais: Se True, exporta arquivos GeoJSON individuais (default True)
    """

    change_to_project_root()

    shp_path = get_ibge_malha_path("RJ_Municipios_2024.shp")
    gdf = gpd.read_file(shp_path)
    print(f"✅ Total de municípios carregados: {len(gdf)}")

    # GeoManager Singleton
    manager = GeoJSONManager()

    # Filtrar os municípios
    selecionados = gdf[gdf["NM_MUN"].isin(municipios)]

    if selecionados.empty:
        print(f"❌ Nenhum município encontrado para: {municipios}")
        return

    if export_individuais:
        for nome in municipios:
            mun_gdf = gdf[gdf["NM_MUN"] == nome]
            if not mun_gdf.empty:
                path = prepare_data_path(
                    "municipios_rj", f"{nome.lower().replace(' ', '_')}.geojson")
                manager.write_geojson(mun_gdf, path)
                print(f"✅ Exportado município individual: {nome} para {path}")

    # União
    union_geom = selecionados.geometry.unary_union
    union_gdf = gpd.GeoDataFrame(geometry=[union_geom], crs=selecionados.crs)

    # Caminho de saída com nome arbitrário
    union_path = prepare_data_path("municipios_rj", output_filename)
    manager.write_geojson(union_gdf, union_path)
    print(f"✅ União dos municípios salva em: {union_path}")


# =======================
# Exemplo de uso
# =======================
if __name__ == "__main__":
    export_municipios_union(
        ["Rio de Janeiro", "Niterói"],
        output_filename="rio_niteroi.geojson",
        export_individuais=True
    )
