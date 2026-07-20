from dataclasses import dataclass

from skyweaver import Parcel, flow, input, node, output


@dataclass
class Number(Parcel):
    value: int = 0


@dataclass
class Doubled(Parcel):
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


def test_flow_call_returns_output_from_current_execution() -> None:
    flow_instance = RepeatedFlow()

    assert flow_instance(3) == 6
    assert flow_instance(4) == 8
