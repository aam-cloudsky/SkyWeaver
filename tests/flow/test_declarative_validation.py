from dataclasses import dataclass

import pytest

from skyweaver import Parcel, flow, input, node, output


@dataclass
class Number(Parcel):
    value: int = 0


@dataclass
class Result(Parcel):
    value: int = 0


def test_async_node_is_rejected_at_definition_time() -> None:
    with pytest.raises(TypeError, match="cannot be async"):

        @flow
        class AsyncFlow:
            @input
            def start(self, value: int) -> Number:
                return Number(value)

            @node
            async def invalid(self, number: Number) -> Result:
                return Result(number.value)

            @output
            def finish(self, result: Result) -> int:
                return result.value


def test_varargs_are_rejected_at_definition_time() -> None:
    with pytest.raises(TypeError, match="cannot declare \\*args or \\*\\*kwargs"):

        @flow
        class VarArgsFlow:
            @node
            def invalid(self, *args) -> Result:
                return Result(0)
