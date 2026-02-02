# core/bus/id_manager.py

from dataclasses import dataclass
from typing import Dict, Optional

from skyweaver.core.bus.enums.reserved_id_enum import ReservedIDs


@dataclass(frozen=True)
class IDRecord:
    owner: object
    id: int
    label: Optional[str] = None


class IDManager:
    """
    Manages stable bus IDs for runtime objects.

    Design invariants:
    - IDs are bound to object *identity*, not equality
    - No requirement for __hash__ or __eq__
    - IDs are monotonically increasing
    - Reserved IDs are declared by the owner itself (__bus_id__)
    """

    def __init__(self):
        # id -> record
        self._by_id: Dict[int, IDRecord] = {}

        # id(owner) -> id
        self._by_owner_id: Dict[int, int] = {}

        # start after reserved IDs
        self._counter: int = max(r.value for r in ReservedIDs)


    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def get_or_create_id(self, owner: object) -> int:
        owner_identity = id(owner)

        if owner_identity in self._by_owner_id:
            return self._by_owner_id[owner_identity]

        reserved = getattr(owner, "__bus_id__", None)

        if reserved is not None:
            self._register_reserved(owner, reserved)
            return reserved

        return self._register(owner)
    
    def _register_reserved(self, owner: object, reserved_id: int) -> None:
        record = IDRecord(owner=owner, id=reserved_id)

        self._by_id[reserved_id] = record
        self._by_owner_id[id(owner)] = reserved_id



    def release_id(self, publisher_id: int) -> None:
        """
        Explicitly release an ID when the publisher lifecycle ends.
        """
        record = self._by_id.pop(publisher_id, None)
        if record is not None:
            self._by_owner_id.pop(id(record.owner), None)

    # -------------------------------------------------
    # Internal mechanics
    # -------------------------------------------------

    def _register(self, owner: object) -> int:
        new_id = self._gen_new_id()

        record = IDRecord(owner=owner, id=new_id)

        self._by_id[new_id] = record
        self._by_owner_id[id(owner)] = new_id

        return new_id

    def _gen_new_id(self) -> int:
        self._counter += 1
        return self._counter

    def _reserved_owner_solver(self, owner: object) -> Optional[int]:
        """
        Owners may declare a reserved bus ID by defining __bus_id__.
        """
        return getattr(owner, "__bus_id__", None)
