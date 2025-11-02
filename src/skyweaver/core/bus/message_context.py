from dataclasses import dataclass, field
from skyweaver.core.bus.reserved_id_enum import ReservedIDs


@dataclass
class MessageContext:
    from_id: int = field(default_factory=int)
    to_id: int = ReservedIDs.BROADCAST.value
    exclude_ids: list[int] = field(default_factory=list)

    
    
