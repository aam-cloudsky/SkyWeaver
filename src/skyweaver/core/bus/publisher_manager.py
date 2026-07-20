from dataclasses import dataclass
from typing import Dict, Type


# core/bus/id_manager.py

from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum, IntEnum, auto


class PublisherID(int):

    def __new__(cls, value):
        return int.__new__(cls, int(value))

    def __repr__(self):
        return f"p:{int(self)}"


class PublisherReservedIDs(PublisherID, Enum):
    """Special routing identifiers for message delivery."""

    BROADCAST = auto()
    LOGGER = auto()
    DEPOT = auto()


@dataclass(frozen=True)
class IDRecord:
    owner: object
    id: int
    label: Optional[str] = None


@dataclass(frozen=True)
class Publisher:
    pid: PublisherID
    owner_type: Type
    label: str
    owner_id: int


class PublisherIDManager:
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
        self._counter: int = max(PublisherReservedIDs)

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


class PublisherManager:

    def __init__(self):
        self._id_manager = PublisherIDManager()
        self._publishers: Dict[PublisherID, Publisher] = {}
        self._owner_index: Dict[int, PublisherID] = {}

    # -------------------------------------------------
    # Registration
    # -------------------------------------------------

    def add_publisher(self, owner: object) -> PublisherID:

        owner_id = id(owner)

        existing_pid = self._owner_index.get(owner_id)
        if existing_pid is not None:
            return existing_pid

        raw_id = self._id_manager.get_or_create_id(owner)
        pid = PublisherID(raw_id)

        publisher = Publisher(
            pid=pid,
            owner_type=type(owner),
            label=owner.__class__.__name__,
            owner_id=owner_id,
        )

        self._publishers[pid] = publisher
        self._owner_index[owner_id] = pid

        return pid

    # -------------------------------------------------
    # Lookup
    # -------------------------------------------------

    def get(self, pid: PublisherID) -> Optional[Publisher]:
        return self._publishers.get(pid)

    def get_by_owner(self, owner: object) -> Optional[Publisher]:

        pid = self._owner_index.get(id(owner))
        if pid is None:
            return None

        return self._publishers.get(pid)

    def get_pid(self, owner: object) -> Optional[PublisherID]:
        return self._owner_index.get(id(owner))

    # -------------------------------------------------
    # Removal
    # -------------------------------------------------

    def remove(self, pid: PublisherID) -> None:
        """
        Removes a publisher by PublisherID and cleans all indexes.
        """
        publisher = self._publishers.pop(pid, None)
        if publisher is None:
            return

        self._owner_index.pop(publisher.owner_id, None)
        self._id_manager.release_id(int(pid))

    def remove_owner(self, owner: object) -> None:

        pid = self._owner_index.get(id(owner))
        if pid is not None:
            self.remove(pid)

    # -------------------------------------------------
    # Introspection
    # -------------------------------------------------

    def all(self) -> Dict[PublisherID, Publisher]:
        return dict(self._publishers)
