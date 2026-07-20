from dataclasses import dataclass

import pytest

from skyweaver import Parcel, flow, input, node
from skyweaver.core.bus.publisher_manager import PublisherReservedIDs
from skyweaver.core.logistics.validity.dependency_registry import (
    DuplicateProducerError,
)


@dataclass
class Source(Parcel):
    value: int = 0


@dataclass
class Product(Parcel):
    value: int = 0


@flow
class BrokenFlow:
    @input
    def start(self, value: int) -> Source:
        return Source(value)

    @node
    def first(self, source: Source) -> Product:
        return Product(source.value)

    @node
    def duplicate(self, source: Source) -> Product:
        return Product(source.value + 1)


def test_materialization_failure_leaves_no_partial_runtime_state() -> None:
    flow_instance = BrokenFlow()

    with pytest.raises(DuplicateProducerError):
        flow_instance(1)

    assert flow_instance._materialized is False
    assert flow_instance._nodes == {}

    hub = flow_instance.logistics._bus._hub

    assert set(hub.publisher_manager._publishers) == {PublisherReservedIDs.DEPOT}
    assert flow_instance.logistics.depot.sentinel._registry.modules() == set()

    for broker in hub._brokers.values():
        for subscribers in broker._subscribers.values():
            assert set(subscribers) == {PublisherReservedIDs.DEPOT}
