from __future__ import annotations

from typing import Any, Generic, Optional, ParamSpec, TypeVar

from skyweaver.core.flow.node.node_definition import (
    ExternalParameter,
    NodeDefinition,
    NodeKind,
)
from skyweaver.core.identifier.identifier import FlowId


class FlowDefinition:
    """
    Immutable declarative description of a Flow.

    A FlowDefinition contains only metadata extracted from the user class.
    It does not own runtime state, Nodes or Logistics.
    """

    def __init__(
        self,
        flow_type: type[Any],
    ) -> None:
        self._flow_type = flow_type
        self.identity = FlowId(flow_type.__name__)
        self.node_definitions = self._collect_nodes()
        self._validate()

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def qualified_name(self) -> str:
        return f"{self._flow_type.__module__}." f"{self._flow_type.__qualname__}"

    @property
    def user_flow_type(self) -> type[Any]:
        return self._flow_type

    @property
    def input_definition(self) -> Optional[NodeDefinition]:
        """
        Returns the single input node definition declared by this Flow.

        Raises:
            RuntimeError:
                If the Flow does not declare an input node.
        """

        inputs = self.definitions_by_kind(NodeKind.INPUT)
        return next(iter(inputs.values()), None)

    @property
    def output_definition(self) -> Optional[NodeDefinition]:
        """
        Returns the single output node definition declared by this Flow.

        Raises:
            RuntimeError:
                If the Flow does not declare an output node.
        """

        outputs = self.definitions_by_kind(NodeKind.OUTPUT)
        return next(iter(outputs.values()), None)

    def _collect_nodes(
        self,
    ) -> dict[str, NodeDefinition]:
        definitions: dict[str, NodeDefinition] = {}

        for flow_type in reversed(self._flow_type.__mro__):
            if flow_type is object:
                continue

            for name, attribute in vars(flow_type).items():
                if isinstance(attribute, NodeDefinition):
                    definitions[name] = attribute

        return definitions

    def definitions_by_kind(
        self,
        kind: NodeKind,
    ) -> dict[str, NodeDefinition]:
        return {
            name: definition
            for name, definition in self.node_definitions.items()
            if definition.kind == kind
        }

    def _validate(self) -> None:

        inputs = self.definitions_by_kind(
            NodeKind.INPUT,
        )

        outputs = self.definitions_by_kind(
            NodeKind.OUTPUT,
        )

        if len(inputs) > 1:
            raise TypeError(
                f"Flow '{self.qualified_name}' declares multiple "
                f"input nodes: {sorted(inputs)}."
            )

        if len(outputs) > 1:
            raise TypeError(
                f"Flow '{self.qualified_name}' declares multiple "
                f"output nodes: {sorted(outputs)}."
            )

    @property
    def input_parameters(
        self,
    ) -> tuple[ExternalParameter, ...]:
        if self.input_definition is None:
            return ()
        return self.input_definition.description.external_parameters

    @property
    def output_type(self):
        if self.output_definition is None:
            return None
        return self.output_definition.description.external_return_type

    @property
    def definitions(
        self,
    ) -> tuple[NodeDefinition, ...]:
        return tuple(self.node_definitions.values())
