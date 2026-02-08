from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.clustering.logistics.cluster_parcel import ClusterParcel
from skyweaver.units.sources.logistics.heliports_parcel import HeliportsParcel
from skyweaver.units.sources.logistics.vertiports_parcel import VertiportsParcel


@dataclass
class ClusterOutpost(Outpost):
    cluster_parcel: ClusterParcel = field(
        default_factory=ClusterParcel, metadata={"role": ParcelRole.PRODUCED}
    )
    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )
    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )
