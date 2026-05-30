# src/skyweaver/planning/graph/graph_outpost.py
from dataclasses import dataclass, field

from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.clustering.logistics.cluster_parcel import ClusterParcel
from skyweaver.units.geodata_domain_alignment.logistics.heliports_parcel import (
    HeliportsParcel,
)
from skyweaver.units.geodata_domain_alignment.logistics.vertiports_parcel import (
    VertiportsParcel,
)
from skyweaver.units.hexgrid.logistics.grid_parcel import GridParcel
from skyweaver.units.routes.logistics.routes_parcel import RoutesParcel
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


@dataclass
class RoutesOutpost(Outpost):
    """
    Declarative structural view of the clustering state within the AirspaceState.

    Each cluster is represented by:
        - a unique ID (e.g., 'UAV_0', 'MAV_1')
        - a set of member points
        - a centroid
        - a boundary (list of perimeter points)
        - a polygon (solid geometric region)
        - a type label ('UAV' or 'MAV')
    """

    routes_parcel: RoutesParcel = field(
        default_factory=RoutesParcel, metadata={"role": ParcelRole.PRODUCED}
    )

    heliports_parcel: HeliportsParcel = field(
        default_factory=HeliportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    vertiports_parcel: VertiportsParcel = field(
        default_factory=VertiportsParcel, metadata={"role": ParcelRole.CONSUMED}
    )

    grid_parcel: GridParcel = field(
        default_factory=GridParcel, metadata={"role": ParcelRole.CONSUMED}
    )
    # TODO: This cluster should be a optional consumed.
    # cluster_parcel: ClusterParcel = field(
    #    default_factory=ClusterParcel, metadata={"role": ParcelRole.CONSUMED}
    # )

    yaml_parcel: YAMLParcel = field(
        default_factory=YAMLParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )
