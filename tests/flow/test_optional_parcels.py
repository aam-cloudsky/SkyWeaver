from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import sys
from pathlib import Path

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
class OptionalProducerFlow:
    @input
    def produce(self, value: int) -> OptionalSource:
        return OptionalSource(value)


@flow
class OptionalConsumerFlow:
    @input
    def trigger(self, value: int) -> Trigger:
        return Trigger(value)

    @node
    def combine(self, trigger: Trigger, source: OptionalSource | None) -> Combined:
        return Combined(trigger.value + (source.value if source is not None else -1))

    @output
    def finish(self, combined: Combined) -> int:
        return combined.value


def test_optional_parcel_is_injected_as_none_when_absent() -> None:
    consumer = OptionalConsumerFlow()

    assert consumer(10) == 9


def test_optional_parcel_is_injected_when_present_in_shared_logistics() -> None:
    producer = OptionalProducerFlow()
    consumer = OptionalConsumerFlow()

    consumer.bind(producer)

    producer(5)

    assert consumer(10) == 15


def test_future_annotations_are_resolved_for_optional_parcels(
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
        return Combined(trigger.value + (source.value if source is not None else -1))

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
    spec.loader.exec_module(module)

    try:
        flow_instance = module.FutureOptionalFlow()
        assert flow_instance(10) == 9
    finally:
        sys.modules.pop(spec.name, None)
