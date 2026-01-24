from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID, uuid4
from skyweaver.core.bus.reserved_id_enum import ReservedIDs


@dataclass
class MessageContext:
    from_id: int = field(default_factory=int)
    to_id: int = ReservedIDs.BROADCAST.value
    exclude_ids: list[int] = field(default_factory=list)
    trace_id: UUID = field(default_factory=uuid4)
    reply_to: Optional[UUID] = None

    
    
