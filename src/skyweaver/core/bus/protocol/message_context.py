from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from skyweaver.core.bus.enums.reserved_id_enum import ReservedIDs


@dataclass
class MessageContext:
    from_id: int = field(default_factory=int)
    to_id: int = ReservedIDs.BROADCAST.value
    exclude_ids: list[int] = field(default_factory=list)
    trace_id: UUID = field(default_factory=uuid4)
    reply_to: Optional[UUID] = None
    _deferred: list = field(default_factory=list)
    _closed: bool = field(default=False)
    _result = None

    def defer(self, func, *args, **kwargs):
        self._deferred.append((func, args, kwargs))

    def flush(self):
        work = self._deferred[:]
        self._deferred.clear()
        for func, args, kwargs in work:
            func(*args, **kwargs)

    def close_transaction(self, result):
        #if self._closed:
        #    raise RuntimeError("Transaction already closed")

        self._closed = True
        self._result = result
