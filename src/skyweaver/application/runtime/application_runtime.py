import threading
from pathlib import Path
from typing import Callable, Optional

from reed import Session

from skyweaver.application.runtime.materialization.scene_materializer import (
    SceneMaterializer,
    SceneSnapshot,
)
from skyweaver.flow import start_session


class ApplicationRuntime:
    """
    Live operational runtime boundary, on top of a Reed session.

    Responsibilities:
    - own the Reed session of SkyWeaver's flow (`skyweaver.flow`);
    - apply each change as one transaction (read the snapshot, compute the
      value to feed, feed, push, read the scene);
    - keep the current scene and notify subscribers when it changes.

    Threads: one lock serializes every use of the session. The startup runs
    on the constructing thread; each intent runs on the thread that calls
    `transact` (a FastAPI worker thread for the HTTP endpoints). Two intents
    therefore never interleave a snapshot read and a feed.

    Runtime pipeline:
        transact(update)
            ↓
        update(snapshot) → value to feed (or None: rejected, nothing runs)
            ↓
        Session.feed(value), Session.push()
            ↓
        SceneSnapshot (the `materialize_scene` node)
            ↓
        Subscribers
    """

    def __init__(
        self,
        config_path: str,
    ):

        self._lock = threading.Lock()
        self._materializer = SceneMaterializer()
        self._callbacks: list[Callable[[SceneSnapshot], None]] = []

        with self._lock:
            self._session: Session = start_session(Path(config_path))
            self._scene: SceneSnapshot = self._session.snapshot()[SceneSnapshot]

    # ======================================================
    # Public API
    # ======================================================

    def get_scene(self) -> SceneSnapshot:
        return self._scene

    def get_transport_scene(self) -> dict:

        return self._materializer.serialize_scene_to_dict(self._scene)

    @property
    def trace(self):
        """Reed's execution trace of the session (bounded ring buffer)."""

        return self._session.trace

    def snapshot(self):
        """The current values of the flow (a Reed snapshot, read only)."""

        with self._lock:
            return self._session.snapshot()

    def transact(self, update: Callable[[object], Optional[object]]) -> bool:
        """
        Apply one change atomically.

        `update` receives the current snapshot and returns the value to
        feed, or `None` to change nothing. Returns whether a value was fed.
        Subscribers are notified once, with the final scene, when the scene
        changed.
        """

        with self._lock:
            value = update(self._session.snapshot())
            if value is None:
                return False

            self._session.feed(value)
            self._session.push()

            scene = self._session.snapshot()[SceneSnapshot]
            if scene is not self._scene:
                self._scene = scene
                for callback in list(self._callbacks):
                    callback(scene)

            return True

    def subscribe(
        self,
        callback: Callable[[SceneSnapshot], None],
    ) -> None:

        self._callbacks.append(callback)

        callback(self._scene)
