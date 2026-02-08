from dataclasses import dataclass, field
from typing import Optional

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.routes.graph.graph_pack import (
    AirspaceGraphPack,
    RoutesGraphPack,
    TerminalsGraphPack,
)


@dataclass
class RoutesParcel(Parcel):
    airspace_graph: AirspaceGraphPack = field(default_factory=AirspaceGraphPack)
    routes_graph: RoutesGraphPack = field(default_factory=RoutesGraphPack)
    terminals_graph: TerminalsGraphPack = field(default_factory=TerminalsGraphPack)
