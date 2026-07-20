from dataclasses import dataclass, field
from typing import Optional

from skyweaver.core.logistics.parcel.parcel import Parcel
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

    def serialize(self):

        return {
            "airspace_graph": {
                "vertices": self.airspace_graph.vcount(),
                "edges": self.airspace_graph.ecount(),
            },
            "terminals_graph": {
                "vertices": self.terminals_graph.vcount(),
                "edges": self.terminals_graph.ecount(),
            },
            "routes": [
                [
                    {
                        "q": cell.coord.q,
                        "r": cell.coord.r,
                    }
                    for cell in path
                ]
                for path in self.routes_graph.paths
            ],
        }
