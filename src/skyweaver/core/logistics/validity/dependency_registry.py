# core/clearance/dependency_registry.py

from typing import Dict, Set, Type, Iterable
from collections import defaultdict

from skyweaver.core.logistics.parcel.parcel import Parcel
from skyweaver.core.logistics.endpoint.role import Role


class DuplicateProducerError(RuntimeError):
    def __init__(
        self,
        *,
        parcel_type: Type[Parcel],
        current_producer: Type,
        new_producer: Type,
    ) -> None:
        super().__init__(
            "DuplicateProducerError\n\n"
            f"Parcel:\n    {parcel_type.__name__}\n\n"
            f"Current producer:\n    {current_producer.__name__}\n\n"
            f"New producer:\n    {new_producer.__name__}\n\n"
            "Only one producer per Parcel type is allowed."
        )


class DependencyRegistry:
    """
    Declarative registry of module dependencies.

    This class does NOT:
    - execute modules
    - resolve execution order
    - observe events

    It only knows:
    - which modules exist
    - which parcels they consume / produce
    - which modules depend on which
    """

    def __init__(self) -> None:
        # module -> parcels it consumes
        self._consumes: Dict[Type, Set[Type[Parcel]]] = defaultdict(set)

        # module -> parcels it produces
        self._produces: Dict[Type, Set[Type[Parcel]]] = defaultdict(set)

        # parcel -> modules that produce it
        self._parcel_producers: Dict[Type[Parcel], Set[Type]] = defaultdict(set)

        # parcel -> modules that consume it
        self._parcel_consumers: Dict[Type[Parcel], Set[Type]] = defaultdict(set)

        # dentro do DependencyRegistry.__init__
        self._mutates: Dict[Type, Set[Type[Parcel]]] = defaultdict(set)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_module(
        self,
        module_type: Type,
        parcels_by_role: Dict[Role, Set[Type[Parcel]]],
    ) -> None:
        """
        Register a module and its declared parcel roles.
        """

        produced = parcels_by_role.get(Role.PRODUCED, set())
        consumed = parcels_by_role.get(Role.CONSUMED, set())
        mutated = parcels_by_role.get(Role.MUTATES, set())

        for parcel in produced:
            existing_producers = self._parcel_producers.get(parcel, set())

            if existing_producers and module_type not in existing_producers:
                current_producer = next(iter(existing_producers))
                raise DuplicateProducerError(
                    parcel_type=parcel,
                    current_producer=current_producer,
                    new_producer=module_type,
                )

            self._produces[module_type].add(parcel)
            self._parcel_producers[parcel].add(module_type)

        for parcel in consumed:
            self._consumes[module_type].add(parcel)
            self._parcel_consumers[parcel].add(module_type)

        for parcel in mutated:
            self._mutates[module_type].add(parcel)

    def unregister_module(
        self,
        module_type: Type,
    ) -> None:
        produced = self._produces.pop(module_type, set())
        consumed = self._consumes.pop(module_type, set())
        mutated = self._mutates.pop(module_type, set())

        for parcel in produced:
            producers = self._parcel_producers.get(parcel)
            if producers is None:
                continue

            producers.discard(module_type)
            if not producers:
                self._parcel_producers.pop(parcel, None)

        for parcel in consumed:
            consumers = self._parcel_consumers.get(parcel)
            if consumers is None:
                continue

            consumers.discard(module_type)
            if not consumers:
                self._parcel_consumers.pop(parcel, None)

    # ------------------------------------------------------------------
    # Queries (structural)
    # ------------------------------------------------------------------

    def modules(self) -> Set[Type]:
        return (
            set(self._produces.keys())
            | set(self._consumes.keys())
            | set(self._mutates.keys())
        )

    def produced_parcels(self, module_type: Type) -> Set[Type[Parcel]]:
        return self._produces.get(module_type, set())

    def consumed_parcels(self, module_type: Type) -> Set[Type[Parcel]]:
        return self._consumes.get(module_type, set())

    def producers_of(self, parcel_type: Type[Parcel]) -> Set[Type]:
        return self._parcel_producers.get(parcel_type, set())

    def consumers_of(self, parcel_type: Type[Parcel]) -> Set[Type]:
        return self._parcel_consumers.get(parcel_type, set())

    # ------------------------------------------------------------------
    # DAG Edges (module → module)
    # ------------------------------------------------------------------

    def upstream_modules(self, module_type: Type) -> Set[Type]:
        """
        Modules that must run BEFORE this module.
        """
        upstream: Set[Type] = set()

        for parcel in self.consumed_parcels(module_type):
            upstream |= self.producers_of(parcel)

        return upstream

    def downstream_modules(self, module_type: Type) -> Set[Type]:
        """
        Modules that depend on this module.
        """
        downstream: Set[Type] = set()

        for parcel in self.produced_parcels(module_type):
            downstream |= self.consumers_of(parcel)

        return downstream

    def dependency_edges(self) -> Set[tuple[Type, Type]]:
        """
        Return all DAG edges (producer → consumer).
        """
        edges: Set[tuple[Type, Type]] = set()

        for parcel, producers in self._parcel_producers.items():
            consumers = self._parcel_consumers.get(parcel, set())
            for p in producers:
                for c in consumers:
                    edges.add((p, c))

        return edges

    def impacted_modules_by_parcels(self, parcels: Set[Type[Parcel]]) -> Set[Type]:
        """
        Given changed parcels, return modules directly impacted
        (i.e. that consume them).
        """
        impacted: Set[Type] = set()
        for parcel in parcels:
            impacted |= self.consumers_of(parcel)
        return impacted

    def impacted_parcels_by_modules(self, modules: Set[Type]) -> Set[Type[Parcel]]:
        """
        Parcels produced by these modules.
        """
        impacted: Set[Type[Parcel]] = set()
        for m in modules:
            impacted |= self.produced_parcels(m)
        return impacted
