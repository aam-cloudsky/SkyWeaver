from dataclasses import dataclass, field

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.domain.frame.domain import Domain


@dataclass(frozen=True)
class DomainParcel(Parcel):
    domain: Domain = field(default_factory=Domain.null)
