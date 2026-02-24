import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from shapely import Point

from skyweaver.core.logistics.depot import Depot
from skyweaver.units.domain.domain_unit import DomainUnit
from skyweaver.units.geodata_domain_alignment.alignment_unit import AlignmentUnit
from skyweaver.units.hexgrid.hexgrid_unit import HexGridUnit
from skyweaver.units.restriction.restriction_unit import RestrictionUnit
from skyweaver.units.routes.routes_unit import RoutesUnit
from skyweaver.units.sources.sources_unit import SourcesUnit
from skyweaver.units.visualization.viz_unit import VisualizationUnit
from skyweaver.units.yaml_loader.yaml_loader_unit import YAMLLoaderUnit


import contextily as ctx
import geopandas as gpd
from shapely.geometry import box

from shapely.geometry import Point as ShapelyPoint
from typing import cast


def parse_args():
    parser = argparse.ArgumentParser(description="SkyWeaver Entry Point")
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file",
    )
    return parser.parse_args()


def main():

    depot = Depot()

    args = parse_args()
    config_path = Path(args.config)

    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        sys.exit(1)

    # =========================
    # 1. Load config
    # =========================
    config_unit = YAMLLoaderUnit(yaml_path=str(config_path))
    config_unit.run()

    print("Configuration loaded successfully.")
    print(config_unit._outpost.yaml_parcel.yaml_fields)
    # =========================
    # 2. Load geodata
    # =========================
    sources_unit = SourcesUnit()
    sources_unit.run()

    print("Geodata loaded successfully.")
    print(sources_unit._outpost.geodata)

    # =========================
    # 3. Build domain
    # =========================
    domain_unit = DomainUnit()
    domain_unit.run()

    print("Domain built successfully. Operational Bounds:")
    print(domain_unit._outpost.domain_parcel.domain.operational_bounds)
    # =========================
    # 4. Align geodata
    # =========================
    alignment_unit = AlignmentUnit()
    alignment_unit.run()

    print("Geodata aligned successfully.")
    print(alignment_unit._outpost.heliports_parcel.heliports)
    print(alignment_unit._outpost.vertiports_parcel.vertiports)
    # =========================
    # 5. Build hex grid
    # =========================
    grid_unit = HexGridUnit()
    grid_unit.run()

    print("Hex grid built successfully.")
    print(grid_unit._outpost.grid_parcel.grid)

    grid = grid_unit._outpost.grid_parcel.grid
    all_cells = list(grid.iter_domain_cells())

    # =========================
    # RESTRICTIONS
    # =========================

    RestrictionUnit().run()

    # =========================
    # ROUTES
    # =========================
    routes_unit = RoutesUnit()
    routes_unit.run()

    routes_graph = routes_unit._outpost.routes_parcel.routes_graph
    routes_graph.ig_graph.summary()

    # =========================
    # 6. Interactive visualization
    # =========================

    grid = grid_unit._outpost.grid_parcel.grid

    def on_left_click(cell):
        """Toggle vertiport (terminal) on cell."""
        vertiports = alignment_unit._outpost.vertiports_parcel.vertiports
        local_center = grid.cartesian_cell_center(cell)

        # Toggle presence in vertiports list (local coordinates)
        existing = [
            p for p in vertiports if p.x == local_center.x and p.y == local_center.y
        ]
        if existing:
            alignment_unit._outpost.vertiports_parcel.vertiports = [
                p
                for p in vertiports
                if not (p.x == local_center.x and p.y == local_center.y)
            ]
        else:
            vertiports.append(local_center)

        # Recompute routes after change
        routes_unit.run()
        viz.run()

    def on_right_click(cell):
        """Toggle cell availability."""
        if cell.is_traversable:
            cell.set_restricted()
        else:
            cell.set_available()

        # Recompute routes after change
        routes_unit.run()
        viz.run()

    viz = VisualizationUnit(
        on_left_click=on_left_click,
        on_right_click=on_right_click,
    )

    viz.run()
    viz.show()

    depot.show_validity()


if __name__ == "__main__":
    main()
