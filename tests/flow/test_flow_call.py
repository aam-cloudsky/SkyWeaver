import pytest
from dataclasses import dataclass

from skyweaver import Parcel, flow, input, node, output
from skyweaver.core.flow.errors import MissingDependencyError


@dataclass
class Number(Parcel):
    value: int = 0


@dataclass
class Doubled(Parcel):
    value: int = 0


@dataclass
class Left(Parcel):
    value: int = 0


@dataclass
class Right(Parcel):
    value: int = 0


@dataclass
class Combined(Parcel):
    value: int = 0


@dataclass
class MaybeValue(Parcel):
    value: int = 0


@flow
class RepeatedFlow:
    @input
    def start(self, value: int) -> Number:
        return Number(value)

    @node
    def double(self, number: Number) -> Doubled:
        return Doubled(number.value * 2)

    @output
    def finish(self, doubled: Doubled) -> int:
        return doubled.value


@flow
class MultiDependencyFlow:
    @input
    def start(self, value: int) -> Number:
        return Number(value)

    @node
    def make_left(self, number: Number) -> Left:
        return Left(number.value + 1)

    @node
    def make_right(self, number: Number) -> Right:
        return Right(number.value + 2)

    @node
    def combine(self, left: Left, right: Right) -> Combined:
        return Combined(left.value + right.value)

    @output
    def finish(self, combined: Combined) -> int:
        return combined.value


@flow
class QueryFlow:
    @output
    def show(self, number: Number) -> int:
        return number.value


@flow
class NullableQueryFlow:
    @output
    def show(self, value: MaybeValue) -> int | None:
        return None


@flow
class MaybeValueProducerFlow:
    @input
    def start(self, value: int) -> MaybeValue:
        return MaybeValue(value)


def test_flow_call_returns_output_from_current_execution() -> None:
    flow_instance = RepeatedFlow()

    assert flow_instance(3) == 6
    assert flow_instance(4) == 8


def test_node_waits_for_all_required_dependencies_before_running() -> None:
    flow_instance = MultiDependencyFlow()

    assert flow_instance(5) == 13


def test_query_flow_raises_when_required_dependency_is_unavailable() -> None:
    flow_instance = QueryFlow()

    with pytest.raises(MissingDependencyError, match="Number"):
        flow_instance()


def test_query_flow_returns_none_when_output_function_returns_none() -> None:
    producer = MaybeValueProducerFlow()
    query = NullableQueryFlow()

    query.bind(producer)
    producer(5)

    assert query() is None
