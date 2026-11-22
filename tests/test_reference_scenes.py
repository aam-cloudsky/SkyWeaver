"""The scenes of the reference sequence equal the recorded ones.

These tests pin the behavior that the migration of SkyWeaver's core to Reed
must preserve. See `reference_harness.py` for the sequence and the rounding.
"""

from __future__ import annotations

from typing import Any

import pytest

import reference_harness as harness


@pytest.fixture(scope="module")
def scenes() -> dict[str, Any]:
    return harness.run_sequence()


@pytest.mark.parametrize("step", [step.name for step in harness.SEQUENCE])
def test_scene_matches_reference(scenes: dict[str, Any], step: str) -> None:
    expected = harness.read_reference(step)
    actual = scenes[step]
    assert harness.layer_summary(actual) == harness.layer_summary(expected), step
    assert actual == expected, f"{step}: scene differs from tests/reference/{step}.json"


def test_websocket_known_defect_no_scene_after_intent() -> None:
    """KNOWN DEFECT, recorded on purpose; this test describes it, it does not endorse it.

    The intent endpoints are synchronous, so they run in a worker thread with
    no event loop, and `SkyWeaverBackend._on_scene_update` calls
    `asyncio.create_task` there; the error is swallowed. A WebSocket client
    therefore receives the startup scene and nothing after an intent, and the
    map updates only after a reconnection. The issue that fixes the defect
    inverts the second assertion (one scene after the intent, equal to
    `01_add_vertiport.json`).
    """

    record = harness.read_reference(harness.WEBSOCKET_RECORD.removesuffix(".json"))
    assert record["known_defect"] == harness.WEBSOCKET_DEFECT
    observed = harness.observe_websocket_after_intent()
    assert observed["initial"] == harness.read_reference("00_startup")
    assert observed["messages_after_intent"] == record["messages_after_intent"] == 0
