
from dataclasses import dataclass, field
from typing import List

from skyweaver.core.logistics.parcel import Parcel


from skyweaver.clustering.cluster import Cluster


@dataclass
class ClusterParcel(Parcel):
    clusters: List[Cluster] = field(default_factory=list)

    def is_resolved(self) -> bool:
        return len(self.clusters) > 0
