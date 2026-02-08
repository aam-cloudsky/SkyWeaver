from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Protocol

from skyweaver.units.grid.geometry.basecell import BaseCell
from skyweaver.units.routes.graph.graph_pack import (
    AirspaceGraphPack,
    RoutesGraphPack,
    TerminalsGraphPack,
)


class MetricResult(Protocol):
    name: str


@dataclass(frozen=True)
class APLResult:
    name: str
    value: float


@dataclass(frozen=True)
class BetweennessResult:
    name: str
    values: Dict[BaseCell, int]


MetricFn = Callable[
    [AirspaceGraphPack, RoutesGraphPack, TerminalsGraphPack],
    MetricResult,
]
