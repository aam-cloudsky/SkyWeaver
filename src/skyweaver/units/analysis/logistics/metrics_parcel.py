from dataclasses import dataclass
from typing import Dict

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.analysis.base import MetricResult


@dataclass
class MetricsParcel(Parcel):
    values: Dict[str, MetricResult]
