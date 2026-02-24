# src/skyweaver/discretization/grid/hexgrid/hexgrid_outpost.py

from dataclasses import dataclass, field
from skyweaver.core.logistics.outpost import Outpost

from skyweaver.core.logistics.parcel import ParcelRole
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.hexgrid.logistics.grid_parcel import GridParcel
from skyweaver.units.yaml_loader.logistics.yaml_parcel import YAMLParcel


@dataclass
class GridOutpost(Outpost):
    """
    Hex grid builder outpost.
    """

    grid_parcel: GridParcel = field(
        default_factory=GridParcel,
        metadata={"role": ParcelRole.PRODUCED},
    )

    domain_parcel: DomainParcel = field(
        default_factory=DomainParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )

    yaml_parcel: YAMLParcel = field(
        default_factory=YAMLParcel,
        metadata={"role": ParcelRole.CONSUMED},
    )
