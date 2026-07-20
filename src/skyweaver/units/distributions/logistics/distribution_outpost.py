from dataclasses import dataclass, field


from skyweaver.core.logistics.endpoint.outpost import Outpost
from skyweaver.core.logistics.parcel.parcel import Parcel
from skyweaver.distributions.logistics.airspace_points import AirspacePoints


@dataclass
class DistributionOutpost(Outpost):
    """
    Immutable description of the UAV and MAV distribution.
    Instantiating this class automatically updates the current AirspaceState.
    """

    airspace_points: AirspacePoints = field(
        default_factory=lambda: AirspacePoints(domain=((-1000, 1000), (-1000, 1000)))
    )
