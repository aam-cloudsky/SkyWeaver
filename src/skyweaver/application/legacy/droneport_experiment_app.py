from dataclasses import dataclass
from pathlib import Path

from skyweaver.core.logistics.depot import Depot
from skyweaver.units.yaml_loader.yaml_loader_unit import YAMLLoaderUnit
from skyweaver.units.sources.sources_unit import SourcesUnit
from skyweaver.units.domain.domain_unit import DomainUnit
from skyweaver.units.geodata_domain_alignment.alignment_unit import AlignmentUnit
from skyweaver.units.hexgrid.hexgrid_unit import HexGridUnit
from skyweaver.units.restriction.restriction_unit import RestrictionUnit
from skyweaver.units.routes.routes_unit import RoutesUnit
from skyweaver.units.visualization.viz_unit import VisualizationUnit


@dataclass
class DroneportExperimentApp:
    config_path: str

    def run(self) -> None:
        Depot()

        self.yaml_unit = YAMLLoaderUnit(yaml_path=self.config_path)
        self.yaml_unit.run()

        self.sources_unit = SourcesUnit()
        self.sources_unit.run()

        self.domain_unit = DomainUnit()
        self.domain_unit.run()

        self.alignment_unit = AlignmentUnit()
        self.alignment_unit.run()

        self.grid_unit = HexGridUnit()
        self.grid_unit.run()

        self._remove_vertiport_heliport_conflicts()

        self.restriction_unit = RestrictionUnit()
        self.restriction_unit.run()

        self.routes_unit = RoutesUnit()
        self.routes_unit.run()

        routes_graph = self.routes_unit._outpost.routes_parcel.routes_graph
        print(
            f"Loaded {len(self.alignment_unit._outpost.heliports_parcel.heliports)} heliports"
        )
        print(
            f"Loaded {len(self.alignment_unit._outpost.vertiports_parcel.vertiports)} vertiports"
        )
        print(f"Computed {len(routes_graph.paths)} terminal paths")

        self.viz = VisualizationUnit(
            on_left_click=self.on_left_click,
            on_right_click=self.on_right_click,
        )
        self.viz.run()
        self.viz.show()

    def on_left_click(self, cell) -> None:
        print("left click")
        if cell is None:
            return
        if self._is_heliport_cell(cell):
            return

        if self._is_vertiport_cell(cell):
            self.routes_unit.remove_vertiport(cell)
        else:
            self.routes_unit.add_vertiport(cell)

        self.routes_unit.run()
        self.viz.run()

    def on_right_click(self, cell) -> None:
        if cell is None:
            return
        if self._is_heliport_cell(cell):
            return
        if self._is_vertiport_cell(cell):
            return

        if cell.is_traversable:
            cell.set_restricted()
        else:
            cell.set_available()

        self.routes_unit.run()
        self.viz.run()

    def _is_heliport_cell(self, cell) -> bool:
        grid = self.grid_unit._outpost.grid_parcel.grid
        heliport_cells = grid.get_cell_from_cartesians(
            self.alignment_unit._outpost.heliports_parcel.heliports
        )
        return cell in heliport_cells

    def _is_vertiport_cell(self, cell) -> bool:
        grid = self.grid_unit._outpost.grid_parcel.grid
        vertiport_cells = grid.get_cell_from_cartesians(
            self.alignment_unit._outpost.vertiports_parcel.vertiports
        )
        return cell in vertiport_cells

    def _remove_vertiport_heliport_conflicts(self) -> None:
        grid = self.grid_unit._outpost.grid_parcel.grid

        heliports = self.alignment_unit._outpost.heliports_parcel.heliports
        vertiports = self.alignment_unit._outpost.vertiports_parcel.vertiports

        heliport_cells = set(grid.get_cell_from_cartesians(heliports))

        filtered_vertiports = []
        for point in vertiports:
            cell = grid.get_cell_from_cartesian(point)
            if cell is None:
                continue
            if cell in heliport_cells:
                continue
            filtered_vertiports.append(point)

        with self.alignment_unit._outpost:
            self.alignment_unit._outpost.vertiports_parcel.vertiports = (
                filtered_vertiports
            )
