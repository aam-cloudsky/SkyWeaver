# src/skyweaver/core/logistics/sentinel.py


from typing import Dict, Set, Type

from skyweaver.core.bus.protocol.message_context import MessageContext

from skyweaver.core.logistics.depot_messages import DepotRegistry, DepotSet
from skyweaver.core.logistics.parcel.parcel import Parcel
from skyweaver.core.logistics.endpoint.role import Role


from typing import Set, Type

from skyweaver.core.logistics.validity.dependency_registry import (
    DependencyRegistry,
    DuplicateProducerError,
)
from skyweaver.core.logistics.validity.validity_transition import ValidityTransition


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

        self.verify_producer(
            message=message,
            context=context,
        )

        self._registry.register_module(
            module_type=module_type, parcels_by_role=parcels_by_role
        )

        # Inicialmente, parcels produzidos são inválidos
        for p in parcels_by_role.get(Role.PRODUCED, set()):
            self._parcel_validity.setdefault(p, False)

    def unregister(
        self,
        module_type: Type,
    ) -> None:
        produced = set(self._registry.produced_parcels(module_type))

        self._registry.unregister_module(module_type)

        for parcel_type in produced:
            if not self._registry.producers_of(parcel_type):
                self._parcel_validity.pop(parcel_type, None)

    def verify_producer(
        self,
        message: DepotRegistry,
        context: MessageContext,
    ) -> None:
        module_type = context.publisher_type
        produced = message.parcels_by_role.get(Role.PRODUCED, set())

        for parcel_type in produced:
            existing_producers = self._registry.producers_of(parcel_type)

            if existing_producers and module_type not in existing_producers:
                current_producer = next(iter(existing_producers))
                raise DuplicateProducerError(
                    parcel_type=parcel_type,
                    current_producer=current_producer,
                    new_producer=module_type,
                )

    def verify_validity(
        self, message: DepotSet, context: MessageContext
    ) -> ValidityTransition:

        module_type = context.publisher_type

        before = dict(self._parcel_validity)

        # --------------------------------------------
        # Identify parcel roles for THIS module
        # --------------------------------------------
        produced = self._registry.produced_parcels(module_type)
        consumed = self._registry.consumed_parcels(module_type)

        origin_parcels: Set[Type[Parcel]] = {type(p) for p in message.pallet.values()}

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

            produced_downstream = self._registry.impacted_parcels_by_modules(modules)

            for p in produced_downstream:
                if self._parcel_validity.get(p, True):
                    self._parcel_validity[p] = False
                    queue.add(p)

        after = dict(self._parcel_validity)

        became_invalid = {p for p in after if before.get(p, True) and not after[p]}

        became_valid = {p for p in after if not before.get(p, False) and after[p]}

        return ValidityTransition(
            before=before,
            after=after,
            became_invalid=became_invalid,
            became_valid=became_valid,
            origin_pallet=origin_parcels,
            affected_modules=affected_modules,
            execution_order=[],  # resolvido depois
        )
