"""The Reed flow alone (no server) reproduces the reference scenes.

The session is driven as the intent handlers drive it: the rules of
`intent_rules` read the snapshot and return the value to feed.
"""

from __future__ import annotations

import dataclasses
import json
from collections import Counter

import pytest

import reference_harness as harness
from skyweaver import model
from skyweaver.application.handlers import intent_rules
from skyweaver.application.runtime.materialization.scene_materializer import (
    SceneMaterializer,
    SceneSnapshot,
)
from skyweaver.flow import NODES, build_flow, start_session

RULES = {
    "/intent/add-vertiport": intent_rules.add_vertiport,
    "/intent/remove-vertiport": intent_rules.remove_vertiport,
    "/intent/toggle-restriction": intent_rules.toggle_restriction,
}


def scene_of(session) -> dict:
    scene = session.snapshot()[SceneSnapshot]
    transport = SceneMaterializer().serialize_scene_to_dict(scene)
    return harness.canonical(json.loads(json.dumps(transport)))


def apply_intent(session, endpoint: str, payload: dict) -> bool:
    value = RULES[endpoint](session.snapshot(), payload["latitude"], payload["longitude"])
    if value is None:
        return False
    session.feed(value)
    session.push()
    return True


def node_name(node_id: str) -> str:
    return node_id.rsplit(".", 1)[-1]


def firings(session, before: set[str]) -> Counter:
    return Counter(
        node_name(event.node_id)
        for event in session.trace.events
        if event.event_type == "node_started" and event.node_execution_id not in before
    )


def seen(session) -> set[str]:
    return {event.node_execution_id for event in session.trace.events}


@pytest.fixture(scope="module")
def session():
    return start_session(harness.CONFIG_PATH)


def test_reference_sequence_through_the_session() -> None:
    session = start_session(harness.CONFIG_PATH)
    for step in harness.SEQUENCE:
        if step.endpoint is not None:
            assert apply_intent(session, step.endpoint, step.payload), step.name
        assert scene_of(session) == harness.read_reference(step.name), step.name


def test_startup_fires_every_node_once() -> None:
    session = start_session(harness.CONFIG_PATH)
    assert firings(session, set()) == Counter(
        {function.__name__: 1 for function, _ in NODES}
    )


@pytest.mark.parametrize(
    ("endpoint", "payload", "expected"),
    [
        (
            "/intent/add-vertiport",
            harness.VERTIPORT_POINT,
            {"apply_vertiport_edits", "compute_routes", "materialize_scene"},
        ),
        (
            "/intent/toggle-restriction",
            harness.RESTRICTION_POINT,
            {"restrict_cells", "build_airspace_graph", "compute_routes", "materialize_scene"},
        ),
    ],
)
def test_each_intent_fires_routes_and_scene_once(endpoint, payload, expected) -> None:
    session = start_session(harness.CONFIG_PATH)
    before = seen(session)
    assert apply_intent(session, endpoint, payload)
    fired = firings(session, before)
    assert set(fired) == expected
    assert fired["compute_routes"] == 1
    assert fired["materialize_scene"] == 1


def test_a_rejected_intent_feeds_nothing(session) -> None:
    heliport = session.snapshot()[model.Heliports].points[0]
    domain = session.snapshot()[intent_rules.Domain]
    geo = domain.local_to_geo_coord([heliport]).to_crs("EPSG:4326").geometry[0]
    snapshot = session.snapshot()
    assert intent_rules.add_vertiport(snapshot, geo.y, geo.x) is None
    assert intent_rules.toggle_restriction(snapshot, geo.y, geo.x) is None
    assert intent_rules.remove_vertiport(snapshot, geo.y, geo.x) is None


def test_artifact_types_are_frozen() -> None:
    for name in model.__all__:
        cls = getattr(model, name)
        assert dataclasses.is_dataclass(cls), name
        assert cls.__dataclass_params__.frozen, name


def test_the_flow_is_reusable() -> None:
    flow = build_flow()
    first = start_session(harness.CONFIG_PATH, flow)
    second = start_session(harness.CONFIG_PATH, flow)
    assert scene_of(first) == scene_of(second) == harness.read_reference("00_startup")
