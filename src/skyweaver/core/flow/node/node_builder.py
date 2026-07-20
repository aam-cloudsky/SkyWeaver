from __future__ import annotations

from typing import Any
from inspect import Parameter, Signature, iscoroutinefunction, signature
from types import UnionType
from typing import (
    Iterable,
    TypeGuard,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)


from skyweaver.core.flow.node.node import Node
from skyweaver.core.flow.node.node_definition import (
    ConsumedParameter,
    ExternalParameter,
    NodeDefinition,
    NodeDescription,
    NodeKind,
    ParcelType,
)
from skyweaver.core.identifier.identifier import FlowId
from skyweaver.core.logistics.logistics import Logistics
from skyweaver.core.logistics.parcel.parcel import Parcel


from typing import Callable, Generic, ParamSpec, TypeVar


class NodeDescriptionBuilder:
    """
    Builds a NodeDescription from a strongly typed function.

    The node kind is explicitly provided by the decorator:

        @input
        @node
        @output
    """

    def __init__(
        self,
        function: Callable,
        kind: NodeKind,
    ) -> None:
        self._function = function
        self._kind = kind

        self._signature: Signature = signature(function)
        self._type_hints = get_type_hints(function)

    def build(self) -> NodeDescription:
        if iscoroutinefunction(self._function):
            raise TypeError(
                f"Node function '{self._function.__name__}' cannot be async."
            )

        consumed_parameters, external_parameters = self._resolve_parameters()

        produced_types, external_return_type = self._resolve_return()

        description = NodeDescription(
            kind=self._kind,
            function=self._function,
            consumed_parameters=consumed_parameters,
            external_parameters=external_parameters,
            produced_types=produced_types,
            external_return_type=external_return_type,
        )

        self._validate(description)

        return description

    def _iter_declared_parameters(self) -> Iterable[Parameter]:
        parameters = list(self._signature.parameters.values())
        if parameters and parameters[0].name in {"self", "cls"}:
            parameters = parameters[1:]

        return parameters

    def _resolve_parameters(
        self,
    ) -> tuple[
        tuple[ConsumedParameter, ...],
        tuple[ExternalParameter, ...],
    ]:
        consumed_parameters: list[ConsumedParameter] = []
        external_parameters: list[ExternalParameter] = []

        for parameter in self._iter_declared_parameters():
            if parameter.kind in (
                Parameter.VAR_POSITIONAL,
                Parameter.VAR_KEYWORD,
            ):
                raise TypeError(
                    f"Node function '{self._function.__name__}' "
                    "cannot declare *args or **kwargs."
                )

            annotation = self._type_hints.get(parameter.name)

            if annotation is None:
                raise TypeError(
                    f"Parameter '{parameter.name}' from node "
                    f"'{self._function.__name__}' must have "
                    "a type annotation."
                )

            parcel_type = self._resolve_consumed_parcel_type(annotation)

            if parcel_type is not None:
                consumed_parameters.append(
                    (
                        parameter.name,
                        parcel_type,
                    )
                )
            else:
                external_parameters.append(
                    (
                        parameter.name,
                        annotation,
                    )
                )

        return (
            tuple(consumed_parameters),
            tuple(external_parameters),
        )

    def _resolve_return(
        self,
    ) -> tuple[
        tuple[ParcelType, ...],
        object | None,
    ]:
        if "return" not in self._type_hints:
            raise TypeError(
                f"Node function '{self._function.__name__}' "
                "must declare a return type."
            )

        return_annotation = self._type_hints["return"]

        if return_annotation is type(None):
            return (), None

        if self._kind == NodeKind.OUTPUT:
            return (), return_annotation

        parcel_types = self._resolve_parcel_return(return_annotation)

        if parcel_types is not None:
            return parcel_types, None

        return (), return_annotation

    def _resolve_parcel_return(
        self,
        annotation: object,
    ) -> tuple[ParcelType, ...] | None:
        if self._is_parcel_type(annotation):
            return (annotation,)

        origin = get_origin(annotation)

        if origin is not tuple:
            return None

        arguments = get_args(annotation)

        if not arguments:
            raise TypeError(
                f"Node function '{self._function.__name__}' "
                "cannot return an empty tuple."
            )

        if Ellipsis in arguments:
            raise TypeError(
                f"Node function '{self._function.__name__}' "
                "must declare a fixed output tuple, such as "
                "tuple[ParcelA, ParcelB]."
            )

        produced_types: list[ParcelType] = []

        for index, argument in enumerate(arguments):
            if not self._is_parcel_type(argument):
                raise TypeError(
                    f"Return item {index} from node "
                    f"'{self._function.__name__}' must inherit "
                    "from Parcel."
                )

            produced_types.append(argument)

        return tuple(produced_types)

    def _resolve_consumed_parcel_type(
        self,
        annotation: object,
    ) -> ParcelType | None:
        if self._is_parcel_type(annotation):
            return annotation

        origin = get_origin(annotation)

        if origin not in (Union, UnionType):
            return None

        non_none_arguments = [
            argument
            for argument in get_args(annotation)
            if argument is not type(None)
        ]

        if len(non_none_arguments) != 1:
            return None

        candidate = non_none_arguments[0]

        if not self._is_parcel_type(candidate):
            return None

        return candidate

    @staticmethod
    def _is_parcel_type(
        annotation: object,
    ) -> TypeGuard[ParcelType]:
        return isinstance(annotation, type) and issubclass(annotation, Parcel)

    def _validate(
        self,
        description: NodeDescription,
    ) -> None:
        self._validate_unique_parcel_types(description)

        if description.kind == NodeKind.INPUT:
            self._validate_input(description)
            return

        if description.kind == NodeKind.TRANSFORM:
            self._validate_transform(description)
            return

        if description.kind == NodeKind.OUTPUT:
            self._validate_output(description)
            return

        raise ValueError(f"Unsupported node kind: {description.kind!r}.")

    def _validate_input(
        self,
        description: NodeDescription,
    ) -> None:
        if description.consumed_parameters:
            raise TypeError(
                f"Input node '{self._function.__name__}' cannot consume Parcels."
            )

        if not description.produced_types:
            raise TypeError(
                f"Input node '{self._function.__name__}' "
                "must produce at least one Parcel."
            )

        if description.external_return_type is not None:
            raise TypeError(
                f"Input node '{self._function.__name__}' "
                "must return a Parcel or a tuple of Parcels."
            )

    def _validate_transform(
        self,
        description: NodeDescription,
    ) -> None:
        if not description.consumed_parameters:
            raise TypeError(
                f"Transform node '{self._function.__name__}' "
                "must consume at least one Parcel."
            )

        if not description.produced_types:
            raise TypeError(
                f"Transform node '{self._function.__name__}' "
                "must produce at least one Parcel."
            )

        if description.external_return_type is not None:
            raise TypeError(
                f"Transform node '{self._function.__name__}' "
                "must return a Parcel or a tuple of Parcels."
            )

    def _validate_output(
        self,
        description: NodeDescription,
    ) -> None:
        if not description.consumed_parameters:
            raise TypeError(
                f"Output node '{self._function.__name__}' "
                "must consume at least one Parcel."
            )

        if description.produced_types:
            raise TypeError(
                f"Output node '{self._function.__name__}' " "cannot produce Parcels."
            )

        if description.external_parameters:
            raise TypeError(
                f"Output node '{self._function.__name__}' "
                "cannot receive external flow inputs."
            )

        if description.external_return_type is None:
            raise TypeError(
                f"Output node '{self._function.__name__}' "
                "must return at least one external result."
            )

        if self._contains_parcel_type(description.external_return_type):
            raise TypeError(
                f"Output node '{self._function.__name__}' "
                "must return external objects, not Parcels."
            )

    def _contains_parcel_type(
        self,
        annotation: object,
    ) -> bool:
        if self._is_parcel_type(annotation):
            return True

        origin = get_origin(annotation)

        if origin is None:
            return False

        return any(
            self._contains_parcel_type(argument) for argument in get_args(annotation)
        )

    def _validate_unique_parcel_types(
        self,
        description: NodeDescription,
    ) -> None:
        consumed_types = tuple(
            parcel_type for _, parcel_type in description.consumed_parameters
        )

        produced_types = description.produced_types

        if len(set(consumed_types)) != len(consumed_types):
            raise TypeError(
                f"Node '{self._function.__name__}' cannot consume "
                "the same Parcel type more than once."
            )

        if len(set(produced_types)) != len(produced_types):
            raise TypeError(
                f"Node '{self._function.__name__}' cannot produce "
                "the same Parcel type more than once."
            )

        overlapping_types = set(consumed_types) & set(produced_types)

        if overlapping_types:
            type_names = sorted(
                parcel_type.__name__ for parcel_type in overlapping_types
            )

            raise TypeError(
                f"Node '{self._function.__name__}' cannot consume "
                "and produce the same Parcel type: "
                f"{type_names}."
            )


class NodeFactory:

    def __init__(
        self,
        instance: Any,
        logistics: Logistics,
    ) -> None:

        self._instance = instance
        self._logistics = logistics

    def create(
        self,
        flow_id: FlowId,
        definition: NodeDefinition,
        *,
        status_changes_enabled: bool = True,
    ) -> Node:

        function = definition.function.__get__(
            self._instance,
            type(self._instance),
        )

        return Node(
            flow_id=flow_id,
            definition=definition,
            function=function,
            logistics=self._logistics,
            status_changes_enabled=status_changes_enabled,
        )
