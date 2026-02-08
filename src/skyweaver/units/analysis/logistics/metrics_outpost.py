from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.planning.logistics.planning_parcel import PlanningParcel

from .metrics_parcel import MetricsParcel


@dataclass
class MetricsOutpost(Outpost):
    planning: PlanningParcel = field(
        default_factory=PlanningParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    metrics: MetricsParcel = field(
        default_factory=lambda: MetricsParcel(values={}),
        metadata={"role": ParcelRole.PRODUCED},
    )
