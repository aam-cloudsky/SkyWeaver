from __future__ import annotations

from typing import Iterable, Optional

from skyweaver.analysis.runner import run
from skyweaver.core.operations.operational_unit import OperationalUnit

from skyweaver.analysis.logistics.metrics_outpost import MetricsOutpost


class MetricsOperationalUnit(OperationalUnit):
    def __init__(self, outpost: MetricsOutpost, names: Optional[Iterable[str]] = None):
        super().__init__(outpost)
        self._names = names

    def run(self) -> None:
        planning = self.outpost.planning
        if planning is None:
            return

        airspace = planning.airspace_graph
        routes = planning.routes_graph
        terminals = planning.terminals_graph

        if airspace is None or routes is None or terminals is None:
            return

        results = run(self._names, airspace, routes, terminals)

        with self.outpost:
            self.outpost.metrics.values = results
