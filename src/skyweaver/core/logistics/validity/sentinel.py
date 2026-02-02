# src/skyweaver/core/logistics/sentinel.py

from ast import Module
from typing import Dict, Set, Type
from skyweaver.core.bus.runtime.port import Port
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.logistics.depot_messages import DepotRegistry, DepotSet, DepotUpdate
from skyweaver.core.logistics.parcel import Parcel, ParcelRole

from dataclasses import dataclass
from typing import Set, Type

from skyweaver.core.logistics.validity.dependency_registry import DependencyRegistry


@dataclass(frozen=True)
class ValidityTransition:
    # Estado
    before: Dict[Type[Parcel], bool]
    after: Dict[Type[Parcel], bool]

    # Diferença semântica
    became_invalid: Set[Type[Parcel]]
    became_valid: Set[Type[Parcel]]

    # Origem causal
    origin_pallet: Set[Type[Parcel]]

    # Contexto operacional
    affected_modules: Set[Type["Module"]]
    execution_order: list[Type["Module"]]

    def __str__(self) -> str:

        def names(types: Set[Type]) -> str:
            return ", ".join(t.__name__ for t in types) or "∅"

        def state(mapping: Dict[Type, bool]) -> str:
            if not mapping:
                return "∅"
            return ", ".join(
                f"{t.__name__}={'VALID' if v else 'INVALID'}"
                for t, v in sorted(mapping.items(), key=lambda x: x[0].__name__)
            )

        return (
            "\n[ValidityTransition]\n"
            f"  Origin parcels : {names(self.origin_pallet)}\n"
            f"  Became VALID   : {names(self.became_valid)}\n"
            f"  Became INVALID : {names(self.became_invalid)}\n"
            f"  Affected mods  : {names(self.affected_modules)}\n"
            f"  Exec order     : "
            f"{' → '.join(m.__name__ for m in self.execution_order) or '∅'}\n"
            f"  AFTER state    : {state(self.after)}"
        )


class Sentinel:
    """
    Passive watcher of Depot updates.

    Responsibilities:
    - Listen to DepotUpdate events via SET topic
    - Extract changed parcel types
    - Notify the validation/coordination service

    Non-responsibilities:
    - No GET/SET
    - No execution
    - No planning
    """

    def __init__(self):
        self._registry = DependencyRegistry()
        self._parcel_validity: Dict[Type[Parcel], bool] = {}

    def register(self, message: DepotRegistry, context: MessageContext):
        module_type = context.publisher_type
        parcels_by_role = message.parcels_by_role

        self._registry.register_module(
            module_type=module_type,
            parcels_by_role=parcels_by_role
        )

        # Inicialmente, parcels produzidos são inválidos
        for p in parcels_by_role.get(ParcelRole.PRODUCED, set()):
            self._parcel_validity.setdefault(p, False)

    def verify_validity(
        self,
        message: DepotSet,
        context: MessageContext
    ) -> ValidityTransition:

        module_type = context.publisher_type

        before = dict(self._parcel_validity)

        # --------------------------------------------
        # Identify parcel roles for THIS module
        # --------------------------------------------
        produced = self._registry.produced_parcels(module_type)
        consumed = self._registry.consumed_parcels(module_type)

        origin_parcels: Set[Type[Parcel]] = {
            type(p) for p in message.pallet.values()
        }

        produced_parcels = origin_parcels & produced
        mutated_parcels = origin_parcels - produced_parcels - consumed

        # --------------------------------------------
        # 1) VALIDATION: only PRODUCED parcels
        # --------------------------------------------
        for p in produced_parcels:
            self._parcel_validity[p] = True

        # --------------------------------------------
        # 2) INVALIDATION: MUTATES cause downstream invalidation
        # --------------------------------------------
        queue = set(mutated_parcels)
        affected_modules: Set[Type] = set()

        while queue:
            changed = queue.pop()

            modules = self._registry.impacted_modules_by_parcels({changed})
            affected_modules |= modules

            produced_downstream = self._registry.impacted_parcels_by_modules(
                modules)

            for p in produced_downstream:
                if self._parcel_validity.get(p, True):
                    self._parcel_validity[p] = False
                    queue.add(p)

        after = dict(self._parcel_validity)

        became_invalid = {
            p for p in after
            if before.get(p, True) and not after[p]
        }

        became_valid = {
            p for p in after
            if not before.get(p, False) and after[p]
        }

        return ValidityTransition(
            before=before,
            after=after,
            became_invalid=became_invalid,
            became_valid=became_valid,
            origin_pallet=origin_parcels,
            affected_modules=affected_modules,
            execution_order=[]  # resolvido depois
        )
