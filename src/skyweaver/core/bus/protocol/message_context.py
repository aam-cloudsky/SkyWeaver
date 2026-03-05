from dataclasses import dataclass, field
from typing import Optional


from skyweaver.core.bus.runtime.publisher_manager import (
    PublisherID,
    PublisherReservedIDs,
)
from skyweaver.core.bus.runtime.trace_id import TraceID


@dataclass
class MessageContext:
    publisher_type: type
    from_id: PublisherID
    to_id: PublisherID = PublisherReservedIDs.BROADCAST

    exclude_ids: list[PublisherID] = field(default_factory=list)
    trace_id: TraceID = field(default_factory=TraceID)
    reply_to: Optional[TraceID] = None
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
        # if self._closed:
        #    raise RuntimeError("Transaction already closed")

        self._closed = True
        self._result = result
