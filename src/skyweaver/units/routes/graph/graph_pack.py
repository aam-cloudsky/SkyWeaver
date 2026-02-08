from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import igraph as ig

from skyweaver.units.grid.geometry.basecell import BaseCell


@dataclass(frozen=True)
class GraphPack:
    graph: ig.Graph = field(default_factory=ig.Graph)
    _cell_to_vid: Dict[BaseCell, int] = field(default_factory=dict)
    _vid_to_cell: Dict[int, BaseCell] = field(default_factory=dict)

    @property
    def ig_graph(self) -> ig.Graph:
        return self.graph

    def get_vid(self, cell: BaseCell) -> Optional[int]:
        return self._cell_to_vid.get(cell)

    def get_cell(self, vid: int) -> Optional[BaseCell]:
        return self._vid_to_cell.get(vid)

    def has_cell(self, cell: BaseCell) -> bool:
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
    paths: List[List[BaseCell]] = field(default_factory=list)


@dataclass(frozen=True)
class TerminalsGraphPack(GraphPack):
    pass
