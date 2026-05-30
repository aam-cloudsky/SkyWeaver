from typing import Callable

from skyweaver.application.runtime.logistics.runtime_outpost import (
    RuntimeOutpost,
)
from skyweaver.application.runtime.materialization.scene_materializer import (
    SceneMaterializer,
    SceneSnapshot,
)
from skyweaver.application.runtime.runtime_units import RuntimeUnits
from skyweaver.core.logistics.parcel import Parcel


class ApplicationRuntime:
    """
    Live operational runtime boundary.

    Responsibilities:
    - observe synchronized runtime parcels through RuntimeOutpost;
    - coordinate runtime-to-scene materialization;
    - maintain the current externally consumable scene snapshot;
    - notify subscribers whenever runtime state changes.

    Architectural role:
    - RuntimeOutpost performs synchronization.
    - SceneMaterializer performs GIS projection/materialization.
    - ApplicationRuntime coordinates the operational lifecycle.

    Runtime pipeline:
        Runtime Parcels
            ↓
        RuntimeOutpost Synchronization
            ↓
        SceneMaterializer
            ↓
        SceneSnapshot
            ↓
        External Subscribers
    """

    def __init__(
        self,
        config_path: str,
    ):

        self.units = RuntimeUnits(config_path)

        self._outpost = RuntimeOutpost()
        self._materializer = SceneMaterializer()

        self._scene = SceneSnapshot(layers=[])

        self._callbacks: list[Callable[[SceneSnapshot], None]] = []

        self._outpost.set_on_pallet_sync(self._on_pallet_sync)

        self._bootstrap_units()

    # ======================================================
    # Bootstrap
    # ======================================================

    def _bootstrap_units(self) -> None:

        self.units.yaml.run()
        self.units.sources.run()
        self.units.domain.run()
        self.units.alignment.run()
        self.units.grid.run()
        # self.units.restriction.run()

        self.units.routes.run()

    # ======================================================
    # Public API
    # ======================================================

    def get_scene(self) -> SceneSnapshot:
        return self._scene

    def get_transport_scene(self) -> dict:

        return self._materializer.serialize_scene_to_dict(self._scene)

    def subscribe(
        self,
        callback: Callable[[SceneSnapshot], None],
    ) -> None:

        self._callbacks.append(callback)

        callback(self._scene)

        # self._callbacks.append(callback)

    # ======================================================
    # Reactive Synchronization
    # ======================================================

    def _on_pallet_sync(
        self,
        pallet: dict[type[Parcel], Parcel],
    ) -> None:

        scene = self._materializer.materialize(pallet, self._outpost)

        self._scene = scene

        for callback in self._callbacks:
            callback(scene)
