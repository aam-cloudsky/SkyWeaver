from typing import Callable, ParamSpec, TypeVar
from skyweaver.core.flow.flow_definition import FlowDefinition

from skyweaver.core.flow.flow_factory import FlowFactory
from skyweaver.core.flow.node.node_builder import NodeDescriptionBuilder
from skyweaver.core.flow.node.node_definition import (
    NodeDefinition,
    NodeKind,
)


def _build_node_definition(
    function: Callable,
    kind: NodeKind,
) -> NodeDefinition:
    """
    Converts a strongly typed function into a declarative node definition.
    """
    description = NodeDescriptionBuilder(
        function=function,
        kind=kind,
    ).build()

    return NodeDefinition(
        description=description,
    )


def input(
    function: Callable,
) -> NodeDefinition:
    """
    Declares an input node.

    Input nodes receive external flow arguments and produce one or more
    Parcels.
    """

    return _build_node_definition(
        function=function,
        kind=NodeKind.INPUT,
    )


def node(
    function: Callable,
) -> NodeDefinition:
    """
    Declares a transform node.

    Transform nodes consume Parcels and produce Parcels.
    """

    return _build_node_definition(
        function=function,
        kind=NodeKind.TRANSFORM,
    )


def output(
    function: Callable,
) -> NodeDefinition:
    """
    Declares an output node.

    Output nodes consume Parcels and return the external result of the
    Flow.
    """

    return _build_node_definition(
        function=function,
        kind=NodeKind.OUTPUT,
    )


def flow(
    flow_type: type,
) -> FlowFactory:

    definition = FlowDefinition(flow_type)
    return FlowFactory(definition)
