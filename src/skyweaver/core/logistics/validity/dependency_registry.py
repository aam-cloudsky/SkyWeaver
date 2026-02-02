# core/clearance/dependency_registry.py

from typing import Dict, Set, Type, Iterable
from collections import defaultdict

from skyweaver.core.logistics.parcel import Parcel, ParcelRole


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
        self._parcel_producers: Dict[Type[Parcel],
                                     Set[Type]] = defaultdict(set)

        # parcel -> modules that consume it
        self._parcel_consumers: Dict[Type[Parcel],
                                     Set[Type]] = defaultdict(set)
        
        # dentro do DependencyRegistry.__init__
        self._mutates: Dict[Type, Set[Type[Parcel]]] = defaultdict(set)


    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_module(
        self,
        module_type: Type,
        parcels_by_role: Dict[ParcelRole, Set[Type[Parcel]]],
    ) -> None:
        """
        Register a module and its declared parcel roles.
        """

        produced = parcels_by_role.get(ParcelRole.PRODUCED, set())
        consumed = parcels_by_role.get(ParcelRole.CONSUMED, set())
        mutated = parcels_by_role.get(ParcelRole.MUTATES, set())

        for parcel in produced:
            self._produces[module_type].add(parcel)
            self._parcel_producers[parcel].add(module_type)

        for parcel in consumed:
            self._consumes[module_type].add(parcel)
            self._parcel_consumers[parcel].add(module_type)

        for parcel in mutated:
            self._mutates[module_type].add(parcel)


    # ------------------------------------------------------------------
    # Queries (structural)
    # ------------------------------------------------------------------

    def modules(self) -> Set[Type]:
        return set(self._produces.keys()) | set(self._consumes.keys()) | set(self._mutates.keys())

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

    def impacted_modules_by_parcels(
        self,
        parcels: Set[Type[Parcel]]
    ) -> Set[Type]:
        """
        Given changed parcels, return modules directly impacted
        (i.e. that consume them).
        """
        impacted: Set[Type] = set()
        for parcel in parcels:
            impacted |= self.consumers_of(parcel)
        return impacted

    def impacted_parcels_by_modules(
        self,
        modules: Set[Type]
    ) -> Set[Type[Parcel]]:
        """
        Parcels produced by these modules.
        """
        impacted: Set[Type[Parcel]] = set()
        for m in modules:
            impacted |= self.produced_parcels(m)
        return impacted
