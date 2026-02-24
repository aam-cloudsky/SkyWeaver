from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import igraph as ig

from skyweaver.units.hexgrid.structure.hexcell import HexCell


@dataclass(frozen=True)
class GraphPack:
    graph: ig.Graph = field(default_factory=ig.Graph)
    _cell_to_vid: Dict[HexCell, int] = field(default_factory=dict)
    _vid_to_cell: Dict[int, HexCell] = field(default_factory=dict)

    @property
    def ig_graph(self) -> ig.Graph:
        return self.graph

    def get_vid(self, cell: HexCell) -> Optional[int]:
        return self._cell_to_vid.get(cell)

    def get_cell(self, vid: int) -> Optional[HexCell]:
        return self._vid_to_cell.get(vid)

    def has_cell(self, cell: HexCell) -> bool:
        return cell in self._cell_to_vid

    def vcount(self) -> int:
        return self.ig_graph.vcount()

    def ecount(self) -> int:
        return self.ig_graph.ecount()


@dataclass(frozen=True)
class AirspaceGraphPack(GraphPack):
    pass


@dataclass(frozen=True)
class RoutesGraphPack(GraphPack):
    paths: List[List[HexCell]] = field(default_factory=list)


@dataclass(frozen=True)
class TerminalsGraphPack(GraphPack):
    pass
