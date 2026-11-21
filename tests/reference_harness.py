"""Reference scenes: the behavior the core migration must preserve.

The reference sequence drives the backend through its HTTP API, in process,
and records the scene (`GET /scene`) after each step. The recorded files under
`tests/reference/` were produced by the backend before the migration to Reed
(commit `cd02743` with deterministic routing). Coordinates are rounded to `DECIMALS` places before they are
stored or compared, so that the files do not depend on the last bits of the
floating-point arithmetic of one platform.

Record again with `python tools/record_reference_scenes.py`; check that two
recordings agree with `python tools/record_reference_scenes.py --check-determinism`.
"""

from __future__ import annotations

import json
import socket
from collections.abc import Iterator
from contextlib import contextmanager
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "examples" / "droneport_experiment" / "config.yaml"
REFERENCE_DIR = Path(__file__).resolve().parent / "reference"
DECIMALS = 9

# A free cell west of the city (add, then remove the vertiport placed there).
VERTIPORT_POINT = {"latitude": -22.90, "longitude": -43.40}
# The center of the middle cell of route 0 in the startup scene.
RESTRICTION_POINT = {"latitude": -22.903826262966408, "longitude": -43.2654493466201}


@dataclass(frozen=True)
class Step:
    name: str
    endpoint: str | None
    payload: dict[str, float] | None


SEQUENCE: tuple[Step, ...] = (
    Step("00_startup", None, None),
    Step("01_add_vertiport", "/intent/add-vertiport", VERTIPORT_POINT),
    Step("02_remove_vertiport", "/intent/remove-vertiport", VERTIPORT_POINT),
    Step("03_toggle_restriction", "/intent/toggle-restriction", RESTRICTION_POINT),
    Step("04_toggle_restriction_again", "/intent/toggle-restriction", RESTRICTION_POINT),
)


def build_context() -> Any:
    """The application context, wired as `run_server.py` wires it."""

    from skyweaver.application.dispatching.build_dispatcher import build_dispatcher
    from skyweaver.application.runtime.application_context import (
        ApplicationContext,
    )
    from skyweaver.application.runtime.application_runtime import (
        ApplicationRuntime,
    )

    runtime = ApplicationRuntime(config_path=str(CONFIG_PATH))
    context = ApplicationContext(runtime=runtime)
    context.set_dispatcher(build_dispatcher(context))
    return context


def build_app(context: Any | None = None) -> Any:
    """Build the FastAPI app exactly as `run_server.py` does."""

    from skyweaver.api.server import SkyWeaverBackend

    return SkyWeaverBackend().create_app(context or build_context())


def canonical(value: Any) -> Any:
    """Round every float to `DECIMALS` places, recursively."""

    if isinstance(value, float):
        return round(value, DECIMALS)
    if isinstance(value, dict):
        return {key: canonical(item) for key, item in value.items()}
    if isinstance(value, list):
        return [canonical(item) for item in value]
    return value


def run_sequence() -> dict[str, Any]:
    """Run the reference sequence on a fresh app; return the canonical scenes."""

    from fastapi.testclient import TestClient

    client = TestClient(build_app())
    scenes: dict[str, Any] = {}
    for step in SEQUENCE:
        if step.endpoint is not None:
            response = client.post(step.endpoint, json=step.payload)
            assert response.status_code == 200, (step.name, response.text)
            assert response.json() == {"status": "ok"}, step.name
        scenes[step.name] = canonical(client.get("/scene").json())
    return scenes


def dumps(value: Any) -> str:
    return json.dumps(value, indent=1, sort_keys=True) + "\n"


def write_reference(scenes: dict[str, Any], directory: Path = REFERENCE_DIR) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, scene in scenes.items():
        (directory / f"{name}.json").write_text(dumps(scene))
    requests = [
        {"step": step.name, "endpoint": step.endpoint, "payload": step.payload}
        for step in SEQUENCE
    ]
    (directory / "sequence.json").write_text(
        dumps({"config": str(CONFIG_PATH.relative_to(ROOT)), "decimals": DECIMALS,
               "steps": requests})
    )


WEBSOCKET_RECORD = "websocket_known_defect.json"
WEBSOCKET_DEFECT = (
    "KNOWN DEFECT: the intent endpoints run in a worker thread with no event "
    "loop, so SkyWeaverBackend._on_scene_update fails in asyncio.create_task and "
    "no scene reaches the WebSocket after an intent. The issue that fixes it "
    "inverts this record and test_websocket_known_defect_no_scene_after_intent."
)


def write_websocket_record(
    observed: dict[str, Any], startup: Any, directory: Path = REFERENCE_DIR
) -> None:
    record = {
        "known_defect": WEBSOCKET_DEFECT,
        "initial_scene_equals_00_startup": observed["initial"] == startup,
        "intent": {"endpoint": "/intent/add-vertiport", "payload": VERTIPORT_POINT},
        "messages_after_intent": observed["messages_after_intent"],
    }
    (directory / WEBSOCKET_RECORD).write_text(dumps(record))


def read_reference(name: str, directory: Path = REFERENCE_DIR) -> Any:
    return json.loads((directory / f"{name}.json").read_text())


def layer_summary(scene: dict[str, Any]) -> list[tuple[str, int]]:
    return [
        (layer["id"], len(layer["geojson"]["features"])) for layer in scene["layers"]
    ]


# ---------------------------------------------------------------------------
# WebSocket: known defect
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def served(app: Any | None = None) -> Iterator[str]:
    """Serve the app with uvicorn on a free local port; yield its base URL."""

    import uvicorn

    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(app or build_app(), host="127.0.0.1", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 120.0
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("server did not start")
        time.sleep(0.1)
    try:
        yield f"127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def observe_websocket_after_intent(wait_seconds: float = 3.0) -> dict[str, Any]:
    """Serve the app on a real port; report what a WebSocket client receives.

    Returns the canonical scene received on connection and the number of
    messages received during `wait_seconds` after an add-vertiport intent.
    """

    import asyncio

    import httpx
    import websockets

    async def client(host: str) -> dict[str, Any]:
        async with websockets.connect(f"ws://{host}/ws", max_size=None) as websocket:
            initial = canonical(json.loads(await websocket.recv()))
            async with httpx.AsyncClient() as http:
                response = await http.post(
                    f"http://{host}/intent/add-vertiport", json=VERTIPORT_POINT
                )
                response.raise_for_status()
            received = 0
            try:
                while True:
                    await asyncio.wait_for(websocket.recv(), timeout=wait_seconds)
                    received += 1
            except asyncio.TimeoutError:
                pass
        return {"initial": initial, "messages_after_intent": received}

    with served() as host:
        return asyncio.run(client(host))
