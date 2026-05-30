from dataclasses import asdict, dataclass, field

from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.domain.frame.bounds import Bounds
from skyweaver.units.domain.frame.coordinates import ProjectedCoordinate
from skyweaver.units.domain.frame.domain import Domain


@dataclass(frozen=True)
class DomainParcel(Parcel):
    domain: Domain = field(default_factory=Domain.null)

    def serialize(self) -> dict:
        center: ProjectedCoordinate = self.domain.center
        return {
            "center": center.serialize(),
            "operational_bounds": asdict(self.domain.operational_bounds),
            "visualization_bounds": asdict(self.domain.visualization_bounds),
        }
