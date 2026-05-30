import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from importlib.metadata import version
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel


from skyweaver.application.intents.toggle_restriction import (
    ToggleRestriction,
)
from skyweaver.application.intents.add_vertiport import (
    AddVertiport,
)
from skyweaver.application.intents.remove_vertiport import (
    RemoveVertiport,
)
from skyweaver.application.runtime.materialization.scene_materializer import (
    SceneSnapshot,
)

PACKAGE_NAME = "skyweaver"


class ToggleRestrictionPayload(BaseModel):

    latitude: float

    longitude: float


class AddVertiportPayload(BaseModel):

    latitude: float

    longitude: float


class RemoveVertiportPayload(BaseModel):

    latitude: float

    longitude: float


# ======================================================
# IMPORTANT ARCHITECTURAL NOTE
# ======================================================
#
# Parcels are NOT serialized as raw runtime objects.
#
# The frontend must receive frontend-safe projections only.
#
# Example:
# - HexGrid itself should never be transmitted.
# - Instead, parcels expose projected representations:
#     - restricted cells
#     - routes
#     - terminals
#     - bounds
#
# Serialization therefore acts as an application projection layer.
#
# This prevents:
# - leaking runtime internals;
# - gigantic websocket payloads;
# - circular references;
# - frontend coupling to runtime structures.
#
# ======================================================
class SkyWeaverBackend:
    def __init__(self):

        self._scene: dict = {"layers": []}

        self._connections: set[WebSocket] = set()

    def _on_scene_update(
        self,
        scene: SceneSnapshot,
    ) -> None:

        self._scene = self._context.get_transport_scene()

        for websocket in self._connections:
            try:
                asyncio.create_task(websocket.send_json(self._scene))
            except Exception:
                pass

    def create_app(self, context):

        self._context = context
        self._scene = context.get_transport_scene()

        context.subscribe_scene(self._on_scene_update)

        app = FastAPI(
            title=PACKAGE_NAME,
            version=version(PACKAGE_NAME),
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/health")
        def health():

            return {"status": "ok"}

        @app.get("/scene")
        def get_scene():

            return self._scene

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self._connections.add(websocket)
            await websocket.send_json(self._scene)
            try:
                while True:
                    # keep websocket alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self._connections.discard(websocket)

        @app.post("/intent/add-vertiport")
        def add_vertiport(payload: AddVertiportPayload):

            intent = AddVertiport(
                latitude=payload.latitude,
                longitude=payload.longitude,
            )

            context.dispatch(intent)

            return {
                "status": "ok",
            }

        @app.post("/intent/toggle-restriction")
        def toggle_restriction(payload: ToggleRestrictionPayload):

            intent = ToggleRestriction(
                latitude=payload.latitude,
                longitude=payload.longitude,
            )

            context.dispatch(intent)

            return {
                "status": "ok",
            }

        @app.post("/intent/remove-vertiport")
        def remove_vertiport(payload: RemoveVertiportPayload):

            intent = RemoveVertiport(
                latitude=payload.latitude,
                longitude=payload.longitude,
            )

            context.dispatch(intent)

            return {
                "status": "ok",
            }

        return app
