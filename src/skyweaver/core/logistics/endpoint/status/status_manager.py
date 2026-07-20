from __future__ import annotations


from typing import Generic, TypeVar


from skyweaver.core.logistics.endpoint.dependency_descriptor import (
    DependencyDescriptor,
)
from skyweaver.core.logistics.endpoint.status.dirty_flags import DirtyFlag
from skyweaver.core.logistics.endpoint.status.status import Status

TElement = TypeVar("TElement")


class StatusManager(Generic[TElement]):

    def __init__(
        self,
        descriptors: dict[TElement, DependencyDescriptor[TElement]],
    ) -> None:

        flags: dict[TElement, DirtyFlag] = {
            element: DirtyFlag.CLEAN for element in descriptors
        }

        dependency_flags: dict[
            TElement,
            dict[TElement, DirtyFlag],
        ] = {}

        for produced, descriptor in descriptors.items():

            if not descriptor.depends_on:
                continue

            dependency_flags[produced] = {
                dependency: DirtyFlag.CLEAN for dependency in descriptor.depends_on
            }

        self.status = Status(
            flags=flags,
            dependency_flags=dependency_flags,
        )

    # -------------------------------------------------------
    # Dirty Flag
    # -------------------------------------------------------

    def mark_dirty(
        self,
        dependency: TElement,
    ) -> bool:
        """
        Performs dirty propagation.
        Marks the given dependency as DIRTY and propagates this state to every
        produced element that depends on it.

        Returns:
            True if the global status changed (CLEAN → DIRTY),
            False otherwise.

        """

        changed = False

        if self.status.flags[dependency] is DirtyFlag.CLEAN:
            self.status.flags[dependency] = DirtyFlag.DIRTY
            changed = True

        for produced, flags in self.status.dependency_flags.items():

            if dependency not in flags:
                continue

            if flags[dependency] is DirtyFlag.CLEAN:
                flags[dependency] = DirtyFlag.DIRTY

            self.status.flags[produced] = DirtyFlag.DIRTY

        return changed

    def mark_clean(
        self,
        produced: TElement,
    ) -> None:
        """
        Performs clean backpropagation.

        Marks the given produced element as CLEAN and propagates the cleanup
        back through its dependencies.

        A dependency is marked CLEAN only if no other produced element still
        depends on a DIRTY version of it.
        """

        self.status.flags[produced] = DirtyFlag.CLEAN
        self._clean_dependencies(produced)

    def _clean_dependencies(self, produced):
        if produced not in self.status.dependency_flags:
            return

        flags = self.status.dependency_flags[produced]

        for dependency in flags:

            flags[dependency] = DirtyFlag.CLEAN

            dependency_still_dirty = any(
                dependency in produced_flags
                and produced_flags[dependency] is DirtyFlag.DIRTY
                for produced_flags in self.status.dependency_flags.values()
            )

            self.status.flags[dependency] = (
                DirtyFlag.DIRTY if dependency_still_dirty else DirtyFlag.CLEAN
            )

    # -------------------------------------------------------
    # Bulk Operations
    # -------------------------------------------------------

    def clear(self) -> None:

        for element in self.status.flags:
            self.status.flags[element] = DirtyFlag.CLEAN

        for flags in self.status.dependency_flags.values():
            for dependency in flags:
                flags[dependency] = DirtyFlag.CLEAN
