from __future__ import annotations

from typing import Dict, Iterable, Optional

from .base import MetricResult
from .registry import all_metrics, get


def run(
    metrics: Optional[Iterable[str]],
    g0,
    g1,
    g2,
) -> Dict[str, MetricResult]:
    if metrics is None:
        items = list(all_metrics().items())
    else:
        items = [(name, get(name)) for name in metrics]

    return {name: fn(g0, g1, g2) for name, fn in items}
