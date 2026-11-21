from dataclasses import dataclass
from typing import Callable, Optional

from skyweaver.application.dispatching.intent_dispatcher import (
    IntentDispatcher,
)
from skyweaver.application.runtime.application_runtime import (
    ApplicationRuntime,
)
from skyweaver.application.runtime.materialization.scene_materializer import (
    SceneSnapshot,
)


@dataclass
class ApplicationContext:
    """
    Official operational façade of the application layer.

    Responsibilities:
    - expose the runtime scene boundary;
    - expose intent dispatching;
    - isolate external interfaces from runtime internals.

    External interfaces (server/frontend/CLI/etc.) should communicate
    only through this object.
    """

    runtime: ApplicationRuntime
    dispatcher: Optional[IntentDispatcher] = None

    # ======================================================
    # Runtime Lifecycle Wiring
    # ======================================================

    def set_dispatcher(
        self,
        dispatcher: IntentDispatcher,
    ) -> None:

        self.dispatcher = dispatcher

    # ======================================================
    # Scene Runtime API
    # ======================================================

    def subscribe_scene(
        self,
        callback: Callable[[SceneSnapshot], None],
    ) -> None:

        self.runtime.subscribe(callback)

    def get_scene(self) -> SceneSnapshot:

        return self.runtime.get_scene()

    def get_transport_scene(self) -> dict:

        return self.runtime.get_transport_scene()

    # ======================================================
    # Intent Dispatching
    # ======================================================

    def dispatch(self, intent) -> None:
        """
        Dispatch an application intent through the configured dispatcher.

        Responsibilities:
        - isolate external interfaces from handler resolution;
        - route intents into the application command pipeline;
        - preserve separation between transport and operational logic.
        """

        if self.dispatcher is None:
            raise RuntimeError("Dispatcher was not configured")

        self.dispatcher.dispatch(intent)
