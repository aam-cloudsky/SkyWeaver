"""The HTTP and WebSocket contract of the backend, on the Reed runtime."""

from __future__ import annotations

import json
import threading

import httpx
import pytest
from fastapi.testclient import TestClient

import reference_harness as harness
from skyweaver.model import HeliportCells, Vertiports
from skyweaver.units.domain.frame.domain import Domain
from skyweaver.units.hexgrid.structure.hexgrid import HexGrid

INTENTS = (
    "/intent/add-vertiport",
    "/intent/remove-vertiport",
    "/intent/toggle-restriction",
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(harness.build_app())


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scene_shape(client: TestClient) -> None:
    response = client.get("/scene")
    assert response.status_code == 200
    scene = response.json()
    assert list(scene) == ["layers"]
    assert [layer["id"] for layer in scene["layers"]] == ["heliports", "vertiports", "routes"]
    for layer in scene["layers"]:
        assert set(layer) == {"id", "geometry_type", "crs", "geojson"}
        assert layer["crs"] == "EPSG:4326"
        assert layer["geojson"]["type"] == "FeatureCollection"
    kinds = {layer["id"]: layer["geometry_type"] for layer in scene["layers"]}
    assert kinds == {"heliports": "Point", "vertiports": "Point", "routes": "LineString"}


@pytest.mark.parametrize("endpoint", INTENTS)
def test_intent_rejects_a_malformed_payload(client: TestClient, endpoint: str) -> None:
    assert client.post(endpoint, json={"latitude": -22.9}).status_code == 422
    assert client.post(endpoint, json={"latitude": "x", "longitude": 1}).status_code == 422


@pytest.mark.parametrize("endpoint", INTENTS)
def test_intent_outside_the_grid_is_accepted_and_changes_nothing(
    client: TestClient, endpoint: str
) -> None:
    before = client.get("/scene").json()
    response = client.post(endpoint, json={"latitude": 10.0, "longitude": 10.0})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.get("/scene").json() == before


def test_websocket_sends_the_current_scene_on_connection(client: TestClient) -> None:
    with client.websocket_connect("/ws") as websocket:
        assert websocket.receive_json() == client.get("/scene").json()


def free_points(context, n: int) -> list[dict[str, float]]:
    """WGS84 centers of `n` free cells (no heliport, no vertiport), spread apart."""

    snapshot = context.runtime.snapshot()
    grid: HexGrid = snapshot[HexGrid]
    domain: Domain = snapshot[Domain]
    taken = set(snapshot[HeliportCells].coords) | {
        cell.coord for cell in grid.get_cell_from_cartesians(snapshot[Vertiports].points)
    }
    cells = [cell for cell in grid.iter_domain_cells() if cell.coord not in taken]
    chosen = cells[len(cells) // (2 * n) :: len(cells) // n][:n]
    centers = [grid.cartesian_cell_center(cell) for cell in chosen]
    geo = domain.local_to_geo_coord(centers).to_crs("EPSG:4326")
    return [{"latitude": p.y, "longitude": p.x} for p in geo.geometry]


def test_concurrent_intents_lose_no_edit() -> None:
    context = harness.build_context()
    app = harness.build_app(context)
    points = free_points(context, 8)
    barrier = threading.Barrier(len(points))
    errors: list[BaseException] = []

    with harness.served(app) as host:
        start = len(httpx.get(f"http://{host}/scene").json()["layers"][1]["geojson"]["features"])

        def add(point: dict[str, float]) -> None:
            try:
                barrier.wait()
                response = httpx.post(
                    f"http://{host}/intent/add-vertiport", json=point, timeout=120
                )
                assert response.status_code == 200
            except BaseException as error:  # noqa: BLE001
                errors.append(error)

        threads = [threading.Thread(target=add, args=(p,)) for p in points]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        scene = httpx.get(f"http://{host}/scene").json()

    assert not errors
    vertiports = scene["layers"][1]["geojson"]["features"]
    assert len(vertiports) == start + len(points)
    assert json.dumps(scene)  # serializable
