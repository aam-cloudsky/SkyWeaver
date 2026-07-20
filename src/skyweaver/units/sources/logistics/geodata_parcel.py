# src/skyweaver/units/sources/logistics/geodata_parcel.py


from dataclasses import dataclass, field
from skyweaver.core.logistics.parcel.parcel import Parcel

from geopandas import GeoDataFrame


@dataclass(frozen=True)
class GeoDataParcel(Parcel):
    heliports: GeoDataFrame = field(default_factory=GeoDataFrame)
    vertiports: GeoDataFrame = field(default_factory=GeoDataFrame)
