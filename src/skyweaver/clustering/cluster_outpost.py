
from dataclasses import dataclass, field
from skyweaver.distributions.airspace_points import AirspacePoints
from skyweaver.core.logistics.outpost import Outpost
from skyweaver.clustering.cluster_parcel import ClusterParcel

@dataclass
class ClusterOutpost(Outpost):
    airspace_points: AirspacePoints = field(default_factory=AirspacePoints)
    cluster_parcel: ClusterParcel = field(default_factory= ClusterParcel)

    
