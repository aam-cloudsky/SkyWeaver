from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from skyweaver import Parcel, flow, input, node, output


@dataclass
class Trigger(Parcel):
    value: int = 0


@dataclass
class OptionalSource(Parcel):
    value: int = 0


@dataclass
class Combined(Parcel):
    value: int = 0


def test_optional_parcel_dependency_is_rejected_at_definition_time() -> None:
    with pytest.raises(TypeError, match="Optional\\[Parcel\\] is not supported"):

        @flow
        class InvalidOptionalFlow:
            @input
            def trigger(self, value: int) -> Trigger:
                return Trigger(value)

            @node
            def combine(
                self,
                trigger: Trigger,
                source: OptionalSource | None,
            ) -> Combined:
                return Combined(trigger.value)

            @output
            def finish(self, combined: Combined) -> int:
                return combined.value


def test_future_annotations_optional_parcel_dependency_is_rejected(
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "future_optional_flow.py"
    module_path.write_text(
        """
from __future__ import annotations

from dataclasses import dataclass

from skyweaver import Parcel, flow, input, node, output


@dataclass
class Trigger(Parcel):
    value: int = 0


@dataclass
class OptionalSource(Parcel):
    value: int = 0


@dataclass
class Combined(Parcel):
    value: int = 0


@flow
class FutureOptionalFlow:
    @input
    def trigger(self, value: int) -> Trigger:
        return Trigger(value)

    @node
    def combine(self, trigger: Trigger, source: OptionalSource | None) -> Combined:
        return Combined(trigger.value)

    @output
    def finish(self, combined: Combined) -> int:
        return combined.value
""",
        encoding="utf-8",
    )

    spec = importlib.util.spec_from_file_location(
        "future_optional_flow",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module

    try:
        with pytest.raises(TypeError, match="Optional\\[Parcel\\] is not supported"):
            spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
