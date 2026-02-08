from __future__ import annotations

from typing import List, Optional

from shapely.geometry import Point

from skyweaver.units.clustering.zone_type import ZoneType
from skyweaver.core.operations.operational_unit import OperationalUnit
from skyweaver.units.clustering.hdbscan_clustering import HDBSCANClustering
from skyweaver.units.clustering.logistics.cluster_outpost import ClusterOutpost


class ClusterUnit(OperationalUnit[ClusterOutpost]):

    def __init__(self, outpost: Optional[ClusterOutpost] = None):
        if outpost is None:
            outpost = ClusterOutpost()
        super().__init__(outpost)
        self._engine = HDBSCANClustering()

    def run(self) -> None:
        heliports: List[Point] = self._outpost.heliports_parcel.heliports
        vertiports: List[Point] = self._outpost.vertiports_parcel.vertiports

        heli_clusters = self._engine.fit_zone(heliports, ZoneType.MAV)
        verti_clusters = self._engine.fit_zone(vertiports, ZoneType.UAV)

        with self._outpost:
            self._outpost.cluster_parcel.clusters = heli_clusters + verti_clusters
