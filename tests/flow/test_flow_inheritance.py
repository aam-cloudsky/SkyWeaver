from dataclasses import dataclass

from skyweaver import Parcel, flow, input, node, output


@dataclass
class Number(Parcel):
    value: int = 0


@dataclass
class Doubled(Parcel):
    value: int = 0


class BaseFlow:
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
class InheritedFlow(BaseFlow):
    pass


@flow
class PartialOverrideFlow(BaseFlow):
    @output
    def finish(self, doubled: Doubled) -> int:
        return doubled.value + 1


@flow
class CompleteOverrideFlow(BaseFlow):
    @input
    def start(self, value: int) -> Number:
        return Number(value + 1)

    @node
    def double(self, number: Number) -> Doubled:
        return Doubled(number.value * 3)

    @output
    def finish(self, doubled: Doubled) -> int:
        return doubled.value - 2


def test_flow_inherits_annotated_methods_from_base_class() -> None:
    flow_instance = InheritedFlow()

    assert flow_instance(3) == 6


def test_flow_partial_override_respects_python_mro() -> None:
    flow_instance = PartialOverrideFlow()

    assert flow_instance(3) == 7


def test_flow_complete_override_replaces_base_annotated_methods() -> None:
    flow_instance = CompleteOverrideFlow()

    assert flow_instance(3) == 10
