from __future__ import annotations
from typing import Generic, ParamSpec, TypeVar


from skyweaver.core.flow.flow import Flow
from skyweaver.core.flow.flow_definition import FlowDefinition

P = ParamSpec("P")
R = TypeVar("R")


class FlowFactory:
    """
    Factory responsible for creating independent Flow instances
    from a shared declarative definition.
    """

    def __init__(
        self,
        definition: FlowDefinition,
    ) -> None:
        self._definition = definition

    @property
    def definition(self) -> FlowDefinition:
        return self._definition

    def __call__(
        self,
        *args,
        **kwargs,
    ):

        instance = self._definition.user_flow_type(
            *args,
            **kwargs,
        )

        return Flow(
            definition=self._definition,
            instance=instance,
        )
