# skyweaver/core/logistics/lifecycle.py

from dataclasses import dataclass
from enum import Enum, auto

from skyweaver.core.bus.protocol.base_message import BaseMessage


class LifecycleState(Enum):
    JOINED = auto()
    READY = auto()
    ACTIVE = auto()
    BUSY = auto()
    ERROR = auto()



@dataclass(frozen=True)
class LifecycleStateMessage(BaseMessage):
    state: LifecycleState
