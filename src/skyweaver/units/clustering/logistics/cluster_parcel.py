from dataclasses import dataclass, field
from typing import List

from skyweaver.core.logistics.parcel import Parcel


from skyweaver.units.clustering.cluster import Cluster


@dataclass
class ClusterParcel(Parcel):
    clusters: List[Cluster] = field(default_factory=list)
