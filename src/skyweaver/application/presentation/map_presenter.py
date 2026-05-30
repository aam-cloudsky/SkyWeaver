from typing import Any, Callable

from skyweaver.application.runtime.logistics.runtime_outpost import (
    RuntimeOutpost,
)
from skyweaver.core.logistics.parcel import Parcel
from skyweaver.units.domain.logistics.domain_parcel import DomainParcel
from skyweaver.units.geodata_domain_alignment.logistics.heliports_parcel import (
    HeliportsParcel,
)
from skyweaver.units.geodata_domain_alignment.logistics.vertiports_parcel import (
    VertiportsParcel,
)
from skyweaver.units.hexgrid.logistics.grid_parcel import GridParcel
from skyweaver.units.routes.logistics.routes_parcel import RoutesParcel


class Runtime:
    """
    Live operational runtime boundary.

    Responsibilities:
    - Observe runtime parcels through a dedicated RuntimeOutpost.
    - Maintain synchronized externally consumable state.
    - Convert runtime structures into frontend-safe payloads.
    - Notify subscribers whenever runtime state changes.

    This object represents the alive operational runtime lifecycle.
    """

    def __init__(self):

        self._outpost = RuntimeOutpost()

        self._state: dict[str, Any] = {}
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []

        self._outpost.set_on_pallet_sync(self._on_pallet_sync)

    # ======================================================
    # Public API
    # ======================================================

    def get_state(self) -> dict[str, Any]:
        return self._state

    def subscribe(
        self,
        callback: Callable[[dict[str, Any]], None],
    ) -> None:

        self._callbacks.append(callback)

    # ======================================================
    # Reactive Runtime Synchronization
    # ======================================================

    def _on_pallet_sync(
        self,
        pallet: dict[type[Parcel], Parcel],
    ) -> None:

        state: dict[str, Any] = {}

        domain_parcel = pallet.get(DomainParcel)
        grid_parcel = pallet.get(GridParcel)
        heliports_parcel = pallet.get(HeliportsParcel)
        vertiports_parcel = pallet.get(VertiportsParcel)
        routes_parcel = pallet.get(RoutesParcel)

        if domain_parcel is not None:
            state["domain"] = domain_parcel.serialize()

        if grid_parcel is not None:
            state["grid"] = grid_parcel.serialize()

        if heliports_parcel is not None:
            state["heliports"] = heliports_parcel.serialize()

        if vertiports_parcel is not None:
            state["vertiports"] = vertiports_parcel.serialize()

        if routes_parcel is not None:
            state["routes"] = routes_parcel.serialize()

        for callback in self._callbacks:
            callback(state)

        self._state = state
