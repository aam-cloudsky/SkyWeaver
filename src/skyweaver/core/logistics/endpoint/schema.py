from collections import defaultdict
from dataclasses import dataclass, fields, field
from types import UnionType
from typing import (
    ClassVar,
    Generic,
    Optional,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from skyweaver.core.logistics.endpoint.dependency_descriptor import (
    DependencyDescriptor,
)
from skyweaver.core.logistics.endpoint.role import Role
from skyweaver.core.logistics.parcel.parcel import Parcel
from skyweaver.core.logistics.parcel.provenance import ParcelVersion

ParcelType = type[Parcel]
ParcelDescriptor = DependencyDescriptor[ParcelType]

TElement = TypeVar("TElement")


@dataclass(frozen=True)
class Schema(Generic[TElement]):
    """
    Compiled structural description of an Outpost.

    A Schema is produced by inspecting the Outpost declaration and
    extracting the structural information required by the logistics layer.

    It contains two complementary projections:

    - types_by_role:
        Groups every declared element according to its synchronization role
        (CONSUMED, PRODUCED, MUTATES).

    - descriptors:
        Structural descriptors of every declared element.

        Produced elements record their dependency graph, whereas consumed
        and mutated elements have an empty dependency set.
    """

    types_by_role: dict[Role, set[TElement]]
    descriptors: dict[TElement, DependencyDescriptor[TElement]]

    _descriptors_by_role: dict[
        Role,
        dict[TElement, DependencyDescriptor[TElement]],
    ] = field(
        init=False,
        repr=False,
    )

    _types: set[TElement] = field(
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        descriptors_by_role = {
            role: {
                element: self.descriptors[element]
                for element in elements
                if element in self.descriptors
            }
            for role, elements in self.types_by_role.items()
        }

        all_types: set[TElement] = set()

        for elements in self.types_by_role.values():
            all_types.update(elements)

        object.__setattr__(
            self,
            "_descriptors_by_role",
            descriptors_by_role,
        )

        object.__setattr__(
            self,
            "_types",
            all_types,
        )

    def descriptors_by_role(
        self,
        role: Role,
    ) -> dict[TElement, DependencyDescriptor[TElement]]:
        return self._descriptors_by_role.get(role, {})

    def types(self) -> set[TElement]:
        return self._types

    def descriptor(
        self,
        element: TElement,
    ) -> DependencyDescriptor[TElement]:
        return self.descriptors[element]


@dataclass(eq=False)
class SchemaBuilder:
    """
    Compiles and exposes the structural schema declared by an Outpost.

    Besides schema compilation, this class provides runtime helpers for
    accessing declared Parcels according to the compiled schema.
    """

    _SCHEMA: ClassVar[Optional["Schema[ParcelType]"]] = None

    # ======================================================
    # Public API
    # ======================================================

    @classmethod
    def schema(cls) -> "Schema[ParcelType]":

        if cls._SCHEMA is None:
            cls._SCHEMA = cls._build_schema()

        return cls._SCHEMA

    @classmethod
    def rebuild_schema(cls) -> "Schema[ParcelType]":
        cls._SCHEMA = cls._build_schema()
        return cls._SCHEMA

    # ======================================================
    # Schema compilation
    # ======================================================

    @property
    def _schema(self) -> Schema[ParcelType]:
        return type(self).schema()

    @classmethod
    def _build_schema(cls) -> "Schema[ParcelType]":

        types_by_role = cls._build_types_by_role()

        return Schema(
            types_by_role=types_by_role,
            descriptors=cls._build_descriptors(types_by_role),
        )

    @classmethod
    def _build_types_by_role(
        cls,
    ) -> dict[Role, set[ParcelType]]:

        roles: dict[Role, set[ParcelType]] = defaultdict(set)
        annotations = get_type_hints(cls)

        for dataclass_field in fields(cls):
            parcel_type, _ = cls._resolve_parcel_annotation(
                annotations.get(dataclass_field.name),
            )

            if parcel_type is None:
                continue

            role = dataclass_field.metadata.get(
                "role",
                Role.UNDEFINED,
            )

            roles[role].add(parcel_type)

        return dict(roles)

    @classmethod
    def _build_descriptors(
        cls,
        types_by_role: dict[Role, set[ParcelType]],
    ) -> dict[
        ParcelType,
        ParcelDescriptor,
    ]:

        descriptors: dict[
            ParcelType,
            ParcelDescriptor,
        ] = {}

        annotations = get_type_hints(cls)
        consumed_types = types_by_role.get(Role.CONSUMED, set())
        optional_consumed_types: set[ParcelType] = set()

        for dataclass_field in fields(cls):
            parcel_type, is_optional = cls._resolve_parcel_annotation(
                annotations.get(dataclass_field.name),
            )

            if parcel_type is None:
                continue

            role = dataclass_field.metadata.get(
                "role",
                Role.UNDEFINED,
            )

            if role == Role.CONSUMED and is_optional:
                optional_consumed_types.add(parcel_type)

        for dataclass_field in fields(cls):
            parcel_type, is_optional = cls._resolve_parcel_annotation(
                annotations.get(dataclass_field.name),
            )

            if parcel_type is None:
                continue

            role = dataclass_field.metadata.get(
                "role",
                Role.UNDEFINED,
            )

            descriptors[parcel_type] = DependencyDescriptor(
                type_=parcel_type,
                field_name=dataclass_field.name,
                depends_on=(set(consumed_types) if role == Role.PRODUCED else set()),
                is_optional=is_optional,
                optional_depends_on=(
                    set(optional_consumed_types) if role == Role.PRODUCED else set()
                ),
            )

        return descriptors

    # ======================================================
    # Inspection
    # ======================================================

    def parcel(
        self,
        parcel_type: ParcelType,
    ) -> Optional[Parcel]:
        return self._parcel(
            self._schema.descriptor(parcel_type),
        )

    def consumed_parcels(self) -> dict[ParcelType, Parcel]:
        return self.parcels_by_role(
            Role.CONSUMED,
            required=True,
        )

    def produced_parcels(self) -> dict[ParcelType, Parcel]:
        return self.parcels_by_role(
            Role.PRODUCED,
        )

    def dependency_versions_of(
        self,
        produced_type: ParcelType,
    ) -> dict[ParcelType, ParcelVersion]:
        return {
            parcel_type: parcel.version
            for parcel_type, parcel in self.dependencies_of(
                produced_type,
            ).items()
        }

    def dependencies_of(
        self,
        produced_type: ParcelType,
    ) -> dict[ParcelType, Parcel]:

        produced_descriptor = self._schema.descriptor(produced_type)

        dependencies: dict[ParcelType, Parcel] = {}

        for dependency_type in produced_descriptor.depends_on:

            dependency_descriptor = self._schema.descriptor(
                dependency_type,
            )

            dependency = self._parcel(
                dependency_descriptor,
            )

            if dependency is None:
                if dependency_descriptor.is_optional:
                    continue
                raise RuntimeError(...)

            dependencies[dependency_type] = dependency

        return dependencies

    # ======================================================
    # Internal helpers
    # ======================================================

    def _parcel(
        self,
        descriptor: ParcelDescriptor,
    ) -> Optional[Parcel]:

        return cast(
            Optional[Parcel],
            getattr(
                self,
                descriptor.field_name,
            ),
        )

    @staticmethod
    def _resolve_parcel_annotation(
        annotation: object | None,
    ) -> tuple[Optional[ParcelType], bool]:
        if annotation is None:
            return None, False

        is_optional = False
        origin = get_origin(annotation)

        if origin in (
            Union,
            UnionType,
        ):

            non_none_types = [
                argument
                for argument in get_args(annotation)
                if argument is not type(None)
            ]

            if len(non_none_types) != 1:
                return None, False

            annotation = non_none_types[0]
            is_optional = True

        if not isinstance(annotation, type):
            return None, False

        if not issubclass(annotation, Parcel):
            return None, False

        return annotation, is_optional

    def parcels_by_role(
        self,
        role: Role,
        *,
        required: bool = False,
    ) -> dict[ParcelType, Parcel]:

        parcels: dict[
            ParcelType,
            Parcel,
        ] = {}

        for parcel_type, descriptor in self._schema.descriptors_by_role(role).items():

            parcel = self._parcel(descriptor)
            if parcel is None:
                if required:
                    raise RuntimeError(
                        f"{role.name.title()} Parcel "
                        f"'{parcel_type.__name__}' is unavailable. "
                        f"Owner: "
                        f"'{type(self).__module__}.{type(self).__qualname__}'. "
                        f"Field: '{descriptor.field_name}'."
                    )

                continue
            parcels[parcel_type] = parcel
        return parcels
