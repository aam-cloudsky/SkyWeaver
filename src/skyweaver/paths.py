import os
from pathlib import Path

# Resolve root as the folder that contains pyproject.toml or README.md
PROJECT_ROOT = Path(__file__).resolve().parents[2]

GEOJSON_DIR = PROJECT_ROOT / "data" / "geojson"


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CHANGE_CWD_CALLED = False


def change_to_project_root():
    """
    Explicitly changes the current working directory to the project root.

    ⚠️ Use with caution!
    This changes the global cwd for the entire Python process.
    Should only be called once per run.

    Prints a warning message on first call.
    """
    global _CHANGE_CWD_CALLED
    if _CHANGE_CWD_CALLED:
        print("❌ ERROR: change_to_project_root() called more than once! Multiple cwd changes are risky and may cause unexpected behavior.")
        return

    os.chdir(_PROJECT_ROOT)
    _CHANGE_CWD_CALLED = True

    print("⚠️ WARNING: Changed cwd to project root. Be aware that this affects the entire Python process.")
    print(f"✅ New cwd: {_PROJECT_ROOT}")


def get_geojson_path(filename: str) -> Path:
    """
    Returns the full path to a GeoJSON file in the data directory.
    
    :param filename: Name of the GeoJSON file.
    :return: Full path to the GeoJSON file.
    """
    return GEOJSON_DIR / filename


def get_ibge_malha_path(filename: str) -> Path:
    """
    Returns the full path to a file inside the IBGE municipal mesh directory.

    :param filename: Name of the file (e.g., .shp, .dbf, etc.).
    :return: Full Path object to the file.
    """
    ibge_dir = PROJECT_ROOT / "data" / "malha_rj_municipios_2024"
    return ibge_dir / filename


PROCESSED_DIR = PROJECT_ROOT / "data" / "municipios_rj"


def get_rj_cities_path(filename: str) -> Path:
    """
    Returns the full path to a processed or derived file in the municipio_rj directory.
    
    :param filename: Name of the processed file.
    :return: Full Path object to the file.
    """
    return PROCESSED_DIR / filename


def is_path_inside_directory(file_path: Path, directory: Path) -> bool:
    """
    Checks if the given file_path is inside the specified directory.

    :param file_path: Path to check.
    :param directory: Directory to check against.
    :return: True if file_path is inside directory, False otherwise.
    """
    try:
        file_path = file_path.resolve()
        directory = directory.resolve()
        return directory in file_path.parents
    except Exception as e:
        print(f"❌ Error checking path containment: {e}")
        return False


def is_geojson_dir(file_path: Path) -> bool:
    """
    Checks if the given file_path is inside the canonical geojson data directory.

    :param file_path: Path to check.
    :return: True if inside data/geojson/, False otherwise.
    """
    return is_path_inside_directory(file_path, GEOJSON_DIR)


def prepare_data_path(subdir_name: str, filename: str) -> Path:
    """
    Ensures a subdirectory exists inside the data folder, and returns the full path for a file.

    :param subdir_name: Name of the subdirectory inside 'data' (e.g., 'municipios_rj').
    :param filename: Name of the file to save.
    :return: Full Path object to the file inside the data subdirectory.
    """
    data_root = Path(__file__).resolve().parents[2] / "data" / subdir_name
    data_root.mkdir(parents=True, exist_ok=True)

    return data_root / filename
