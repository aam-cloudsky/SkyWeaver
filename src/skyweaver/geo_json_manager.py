"""
GeoJSONManager

Singleton responsible for all GeoJSON IO (read/write).
Avoids race conditions and centralizes file access logic.
"""

import geopandas as gpd

# Singleton pattern to ensure only one instance of GeoJSONManager exists
# across the application.
from threading import Lock

from skyweaver.paths import get_geojson_path, is_geojson_dir

class GeoJSONManager:
    _instance = None
    _lock = Lock()  # Ensures thread-safe singleton initialization

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GeoJSONManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return  # Prevent reinitialization
        self._cache = {}  # Optional: in-memory cache of loaded GeoJSON
        self._initialized = True

    def read_geojson(self, file_path, use_cache=True):
        """
        Reads a GeoJSON file into a GeoDataFrame.
        Optionally caches the result to avoid reloading.
        """
        if use_cache and file_path in self._cache:
            print(f"✅ Returning cached GeoJSON for: {file_path}")
            return self._cache[file_path]

        try:
            gdf = gpd.read_file(file_path)
            if use_cache:
                self._cache[file_path] = gdf
            print(f"✅ Successfully read GeoJSON: {file_path}")
            print("CRS:", gdf.crs)
            return gdf
        except Exception as e:
            print(f"❌ Error reading GeoJSON {file_path}: {e}")
            return None



    def _is_forbbiden_paths(self, file_path):
        rules = [is_geojson_dir]

        for rule in rules:
            if rule(file_path):
                print(f"❌ Access denied for path: {file_path}")
                return True
        
        return False

    def write_geojson(self, gdf, file_path):
        """
        Writes a GeoDataFrame to a GeoJSON file.
        """

        if self._is_forbbiden_paths(file_path):
            print(f"❌ Cannot write to GeoJSON directory: {file_path}")
            return
            
        try:
            gdf.to_file(file_path, driver="GeoJSON")
            print(f"✅ Successfully wrote GeoJSON: {file_path}")
        except Exception as e:
            print(f"❌ Error writing GeoJSON {file_path}: {e}")

    def clear_cache(self):
        """
        Clears the in-memory cache.
        """
        self._cache.clear()
        print("⚡ Cache cleared.")

    def remove_from_cache(self, file_path):
        """
        Removes a specific file from cache.
        """
        if file_path in self._cache:
            del self._cache[file_path]
            print(f"⚡ Removed from cache: {file_path}")


# ==============================
# 💬 Example usage
# ==============================

from skyweaver.paths import get_geojson_path, change_to_project_root

if __name__ == "__main__":

    change_to_project_root()
    manager = GeoJSONManager()
    
    geojson_path = get_geojson_path("heliport.geojson")
    # Reading a file
    gdf = manager.read_geojson(geojson_path)

    # Optionally modify gdf here ...

    # Writing a file
    optimized_path = get_geojson_path("heliport_optimized.geojson")
    manager.write_geojson(gdf, optimized_path)

    # Clear cache if needed
    manager.clear_cache()
