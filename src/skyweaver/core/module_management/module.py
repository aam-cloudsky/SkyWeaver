

from typing import Any, Dict, Set, Type

from skyweaver.core.coordination.clearance import Clearance
from skyweaver.core.logistics.outpost import Outpost
from skyweaver.core.logistics.parcel import Parcel, ParcelRole


class Module:
    def __init__(self, outpost: Outpost):
        self.outpost = outpost
        parcels_by_role: Dict[ParcelRole,
                              Set[Type[Parcel]]] = outpost.parcels_by_role()
        self._clearance = Clearance()
        self._clearance.registry(self, parcels_by_role)
