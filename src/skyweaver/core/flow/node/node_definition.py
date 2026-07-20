from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Generic, ParamSpec, TypeAlias, TypeVar


from skyweaver.core.flow.node.propagation_policy import PropagationPolicy
from skyweaver.core.logistics.parcel.parcel import Parcel

ParcelType: TypeAlias = type[Parcel]
# NodeFunction: TypeAlias = Callable[..., object]

ConsumedParameter: TypeAlias = tuple[str, ParcelType]
ExternalParameter: TypeAlias = tuple[str, object]


class NodeKind(Enum):
    INPUT = auto()
    TRANSFORM = auto()
    OUTPUT = auto()


@dataclass(frozen=True)
class NodeDescription:
    """
    Structural description derived from a typed node function.
    """

    kind: NodeKind
    function: Callable

    consumed_parameters: tuple[ConsumedParameter, ...]
    external_parameters: tuple[ExternalParameter, ...]

    produced_types: tuple[ParcelType, ...]
    external_return_type: object | None


@dataclass(frozen=True)
class NodeDefinition:
    """
    Declarative node definition produced by a node decorator.

    It preserves the original function and its resolved structural
    description.
    """

    description: NodeDescription
    propagation_policy: PropagationPolicy = PropagationPolicy.ALL_DEPENDENCIES_CHANGED

    @property
    def name(self) -> str:
        return self.function.__name__

    @property
    def kind(self) -> NodeKind:
        return self.description.kind

    @property
    def function(self) -> Callable:
        return self.description.function
