"""Read the heliports and the candidate vertiports from their files."""

from __future__ import annotations

import pathlib
import random
from typing import List, Tuple

import geopandas as gpd
from shapely.geometry import Point

from skyweaver.model.configuration import Configuration
from skyweaver.model.sites import SourceGeoData
from skyweaver.units.sources.sources_parameters import SourcesParameters


def load_geodata(configuration: Configuration) -> SourceGeoData:
    """Read the two layers named in the `sources` section of the configuration.

    A missing or invalid path gives an empty layer, with a warning.
    """

    parameters = SourcesParameters.from_configuration(configuration)

    heliports = _load_layer(parameters.heliports_path, configuration.config_dir)
    print(f"Loaded {len(heliports)} heliports from {parameters.heliports_path}")
    vertiports = _load_layer(parameters.vertiports_path, configuration.config_dir)

    return SourceGeoData(heliports=heliports, vertiports=vertiports)


def simulate_geodata(
    n_heliports: int = 5,
    n_vertiports: int = 5,
    rng: random.Random | None = None,
) -> SourceGeoData:
    """Random heliports and vertiports inside a random square of 10 km."""

    rng = rng or random.Random()
    domain = (
        (rng.uniform(0, 10000), rng.uniform(0, 10000)),
        (rng.uniform(0, 10000), rng.uniform(0, 10000)),
    )
    heliports = _random_points(domain, n_heliports, rng)
    vertiports = _random_points(domain, n_vertiports, rng)
    return SourceGeoData(
        heliports=gpd.GeoDataFrame(geometry=heliports, crs="EPSG:4326"),
        vertiports=gpd.GeoDataFrame(geometry=vertiports, crs="EPSG:4326"),
    )


def _resolve(path: str, base_dir: pathlib.Path) -> Tuple[str, bool]:
    if not path:
        return path, False

    p = pathlib.Path(path)
    if not p.is_absolute():
        p = (base_dir / p).resolve()

    if not p.exists():
        print(f"[Warning] Path does not exist: {p}")
        return str(p), False

    if not p.is_file():
        print(f"[Warning] Not a file: {p}")
        return str(p), False

    return str(p), True


def _load_layer(path: str, base_dir: pathlib.Path) -> gpd.GeoDataFrame:
    resolved, valid = _resolve(path, base_dir)
    if not valid:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    return gpd.read_file(resolved)


def _random_points(
    domain: Tuple[Tuple[float, float], Tuple[float, float]],
    number: int,
    rng: random.Random,
) -> List[Point]:
    (xmin, xmax), (ymin, ymax) = domain
    return [
        Point(rng.uniform(xmin, xmax), rng.uniform(ymin, ymax)) for _ in range(number)
    ]
