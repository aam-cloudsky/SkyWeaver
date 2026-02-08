from __future__ import annotations

from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.planning.logistics.planning_outpost import PlanningOutpost
from skyweaver.units.traces.graph.graph_builder import GraphBuilder


class GraphOperationalUnit(OperationalUnit[PlanningOutpost]):
    def __init__(self, outpost: PlanningOutpost):
        super().__init__(outpost)

    def run(self) -> None:
        builder = GraphBuilder(outpost=self._outpost)
        airspace = builder.build_airspace_graph()

        with self._outpost:
            self._outpost.planning_parcel.airspace_graph = airspace
