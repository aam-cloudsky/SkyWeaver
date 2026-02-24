from enum import Enum


class EPSG(Enum):
    """EPSG codes are a standard way to identify coordinate reference systems (CRS) used in geospatial applications.
    They are defined by the European Petroleum Survey Group (EPSG) and are widely used in GIS (Geographic Information Systems) and mapping applications.
        - EPSG:4326 is a common CRS that uses latitude and longitude coordinates in degrees.
        It is based on the WGS 84 datum and is often used for global datasets and web mapping applications.
    """

    PROJECTION_IN_DEGREES = "EPSG:4326"
    PROJECTION_IN_METERS = "EPSG:31983"
