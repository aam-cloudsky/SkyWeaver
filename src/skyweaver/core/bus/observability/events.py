# ---------------------------------------------------------------------
# Event Monitor
# ---------------------------------------------------------------------


from dataclasses import dataclass

from skyweaver.core.bus.observability.trace import TraceRecord, TraceState
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.validity_message import ValidityMessage
from skyweaver.core.logistics.lifecycle import LifecycleStateMessage


class MonitorEvent:
    pass


@dataclass
class TraceEvent(MonitorEvent):
    trace: TraceRecord
    state: TraceState
