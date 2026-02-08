from dataclasses import dataclass
from typing import Optional

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.traces.graph.graph_pack import (
    AirspaceGraphPack,
    RoutesGraphPack,
    TerminalsGraphPack,
)


@dataclass
class PlanningParcel(Parcel):
    airspace_graph: Optional[AirspaceGraphPack] = None
    routes_graph: Optional[RoutesGraphPack] = None
    terminals_graph: Optional[TerminalsGraphPack] = None
