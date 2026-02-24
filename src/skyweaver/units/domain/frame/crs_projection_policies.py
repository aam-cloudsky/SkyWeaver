# skyweaver/units/domain/frame/crs_projection_policies.py

from enum import Enum
from abc import ABC, abstractmethod
from pyproj import CRS
import utm as UniversalTransverseMercator


class DatumTypes(Enum):
    WGS84 = "WGS84"


class SystemCRS:
    GEOGRAPHIC = CRS.from_dict({"proj": "longlat", "datum": DatumTypes.WGS84.value})


class ProjectionTypes(Enum):
    MERCATOR = "utm"
    AZIMUTHAL_EQUIDISTANT = "aeqd"


class CRSProjectionPolicy(ABC):

    @abstractmethod
    def from_origin(self, latitude: float, longitude: float) -> CRS:
        pass


class AEQDProjectionPolicy(CRSProjectionPolicy):

    def from_origin(self, latitude: float, longitude: float) -> CRS:

        return CRS.from_dict(
            {
                "proj": ProjectionTypes.AZIMUTHAL_EQUIDISTANT.value,
                "lat_0": latitude,
                "lon_0": longitude,
                "datum": DatumTypes.WGS84.value,
            }
        )


class ZonedTransverseMercatorProjectionPolicy(CRSProjectionPolicy):

    def from_origin(self, latitude: float, longitude: float) -> CRS:

        _, _, zone_number, _ = UniversalTransverseMercator.from_latlon(
            latitude, longitude
        )

        return CRS.from_dict(
            {
                "proj": ProjectionTypes.MERCATOR.value,
                "zone": zone_number,
                "south": latitude < 0,
                "datum": DatumTypes.WGS84.value,
            }
        )
