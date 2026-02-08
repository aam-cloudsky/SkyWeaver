from __future__ import annotations
from typing import Dict

from .base import MetricFn

_METRICS: Dict[str, MetricFn] = {}


def register(name: str):
    def decorator(fn: MetricFn) -> MetricFn:
        if name in _METRICS:
            raise ValueError(f"Metric already registered: {name}")
        _METRICS[name] = fn
        return fn

    return decorator
