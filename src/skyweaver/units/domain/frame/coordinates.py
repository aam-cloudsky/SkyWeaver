# coordinates.py

from dataclasses import dataclass
from pyproj import CRS


@dataclass(frozen=True)
class ProjectedCoordinate:
    x: float
    y: float
    crs: CRS

    @staticmethod
    def default():
        return ProjectedCoordinate(0, 0, CRS.from_epsg(3857))

    def serialize(self):
        return {"x": self.x, "y": self.y, "crs": self.crs.to_json_dict}
