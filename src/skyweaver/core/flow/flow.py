from __future__ import annotations

from typing import ClassVar, cast

from skyweaver.core.flow.flow_definition import FlowDefinition
from skyweaver.core.flow.node.node import Node
from skyweaver.core.flow.node.node_builder import NodeFactory
from skyweaver.core.flow.node.node_definition import NodeDefinition
from skyweaver.core.logistics.logistics import Logistics

from typing import Generic, ParamSpec, TypeVar

P = ParamSpec("P")  # Parameters of the @input node
R = TypeVar("R")  # Return type of the @output node


class Flow(Generic[P, R]):
    """
    Executable Flow.

    Each Flow instance owns its own execution state, while the declarative
    FlowDefinition is shared between all instances of the same subclass.
    """

    def __init__(
        self,
        definition,
        instance,
    ):

        self._definition = definition

        self._definition = definition
        self._instance = instance

        self._nodes: dict[str, Node] = {}
        self._materialized = False

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        if not self._materialized:
            self._create_nodes()

        input_definition = self._definition.input_definition
        output_definition = self._definition.output_definition

        if input_definition is None and output_definition is None:
            raise RuntimeError(
                f"Flow '{self._definition.qualified_name}' is not executable: "
                "it declares neither input nor output nodes."
            )

        if input_definition is not None:
            if output_definition is not None:
                self.output_node.reset_output()
            self.input_node.invoke_input(*args, **kwargs)
        else:
            if args or kwargs:
                raise RuntimeError(
                    f"Flow '{self._definition.qualified_name}' does not declare an input node."
                )

        if output_definition is None:
            return cast(R, None)

        return cast(R, self.output_node.output_result)

    @property
    def input_node(self) -> Node:
        definition = self._definition.input_definition
        if definition is None:
            raise RuntimeError(
                f"Flow '{self._definition.qualified_name}' does not declare an input node."
            )
        return self._node_from_definition(definition)

    @property
    def output_node(self) -> Node:
        definition = self._definition.output_definition
        if definition is None:
            raise RuntimeError(
                f"Flow '{self._definition.qualified_name}' does not declare an output node."
            )
        return self._node_from_definition(definition)

    @property
    def logistics(self) -> Logistics:
        if not hasattr(self, "_logistics"):
            self._logistics = Logistics()
        return self._logistics

    def _node_from_definition(
        self,
        definition: NodeDefinition,
    ) -> Node:
        return self._nodes[definition.name]

    def _create_nodes(self) -> None:

        if self._materialized:
            return

        factory = NodeFactory(
            instance=self._instance,
            logistics=self.logistics,
        )

        created_nodes: dict[str, Node] = {}

        try:
            for definition in self._definition.definitions:
                created_nodes[definition.name] = factory.create(
                    flow_id=self._definition.identity,
                    definition=definition,
                )
        except Exception:
            for node in reversed(tuple(created_nodes.values())):
                node.close()
            raise

        self._nodes = created_nodes

        self._materialized = True

    def bind(self, flow: Flow) -> None:

        if self is flow:
            return

        if self._materialized:
            raise RuntimeError("A Flow cannot be bound after materialization.")

        self._logistics = flow.logistics
