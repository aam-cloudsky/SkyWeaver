import matplotlib.pyplot as plt
import geopandas as gpd
from skyweaver.paths import prepare_data_path, change_to_project_root

change_to_project_root()
gdf = gpd.read_file("data/grids/grid_rio_niteroi_restrito.geojson")
gdf.plot(column="restricted", legend=True, cmap="coolwarm")
plt.title("Células Restritas por Heliponto")
plt.show()
