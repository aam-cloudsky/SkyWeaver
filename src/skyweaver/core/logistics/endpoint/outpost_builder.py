from dataclasses import field, make_dataclass
from typing import Callable, Optional, TypeAlias, cast

from skyweaver.core.flow.node.node_definition import (
    NodeDescription,
    ParcelType,
)

from skyweaver.core.identifier.identifier import FlowId, NodeId, OutpostId
from skyweaver.core.logistics.endpoint.outpost import Outpost
from skyweaver.core.logistics.endpoint.role import Role
from skyweaver.core.logistics.logistics import Logistics
from skyweaver.core.logistics.parcel.parcel import Parcel

NodeResult: TypeAlias = Parcel | tuple[Parcel, ...]
NodeFunction: TypeAlias = Callable[..., NodeResult]


ConsumedParameter: TypeAlias = tuple[str, ParcelType]


class OutpostBuilder:
    def __init__(
        self,
        description: NodeDescription,
    ) -> None:
        self._description = description
        self._outpost_type = self._build_outpost_type()

    def build(
        self,
        *,
        node_id: NodeId,
        logistics: Logistics,
    ) -> Outpost:

        return logistics.create_outpost(self._outpost_type, node_id=node_id)

    def _build_outpost_type(
        self,
    ) -> type[Outpost]:
        generated_fields: list[tuple[str, object, object]] = []

        used_names: set[str] = set()

        for parameter_name, parcel_type in self._description.consumed_parameters:
            used_names.add(parameter_name)

            generated_fields.append(
                (
                    parameter_name,
                    parcel_type,
                    field(
                        default=None,
                        metadata={"role": Role.CONSUMED},
                    ),
                )
            )

        for index, parcel_type in enumerate(self._description.produced_types):
            field_name = self._produced_field_name(
                parcel_type=parcel_type,
                index=index,
                used_names=used_names,
            )

            generated_fields.append(
                (
                    field_name,
                    parcel_type,
                    field(
                        default=None,
                        metadata={"role": Role.PRODUCED},
                    ),
                )
            )

        generated_type = make_dataclass(
            cls_name=(f"{self._description.function.__name__}" "Outpost"),
            fields=generated_fields,
            bases=(Outpost,),
            namespace={
                "__module__": (self._description.function.__module__),
            },
            eq=False,
        )

        return cast(
            type[Outpost],
            generated_type,
        )

    @staticmethod
    def _produced_field_name(
        *,
        parcel_type: ParcelType,
        index: int,
        used_names: set[str],
    ) -> str:
        base_name = f"produced_{parcel_type.__name__}"
        candidate = base_name
        suffix = index

        while candidate in used_names:
            candidate = f"{base_name}_{suffix}"
            suffix += 1

        used_names.add(candidate)
        return candidate
