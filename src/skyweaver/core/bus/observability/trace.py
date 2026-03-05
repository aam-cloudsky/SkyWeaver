from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional


from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.runtime.publisher_manager import PublisherID
from skyweaver.core.bus.runtime.trace_id import TraceID


@dataclass
class TraceRecord:
    trace_id: TraceID
    reply_to: Optional[TraceID]

    topic: TopicsEnum
    origin: PublisherID
    target: PublisherID
    message: BaseMessage

    delivered: bool = False


class TraceState(Enum):
    OK_REQUEST = auto()
    OK_REPLY = auto()
    FAIL_REQUEST = auto()
    FAIL_REPLY = auto()
    TIMEOUT = auto()
    REROUTE_REQUEST = auto()
    REROUTE_REPLY = auto()


@dataclass
class TraceEvent:
    trace: TraceRecord
    state: TraceState


class TraceManager:

    def __init__(self):
        self._traces: Dict[TraceID, TraceRecord] = {}

    # ==========================================================================================
    # Trace Lifecycle
    # ==========================================================================================

    def _gen_trace(
        self, topic: TopicsEnum, message: BaseMessage, context: MessageContext
    ) -> TraceRecord:

        return TraceRecord(
            trace_id=context.trace_id,
            reply_to=context.reply_to,
            topic=topic,
            origin=context.from_id,
            target=context.to_id,
            message=message,
            delivered=False,
        )

    def track(self, topic: TopicsEnum, message: BaseMessage, context: MessageContext):

        trace = self._gen_trace(topic, message, context)
        self._traces[trace.trace_id] = trace

    def close_track(
        self, context: MessageContext, delivered: bool
    ) -> Optional[TraceEvent]:

        trace_id: TraceID = context.trace_id
        trace = self._traces.pop(trace_id, None)
        if not trace:
            return None

        trace.delivered = delivered
        state = self.resolve_trace_state(trace)

        return TraceEvent(trace, state)

    def resolve_trace_state(self, trace: TraceRecord) -> TraceState:
        is_reply = trace.reply_to is not None
        is_delivered = trace.delivered

        if is_delivered and is_reply:
            return TraceState.OK_REPLY
        if is_delivered:
            return TraceState.OK_REQUEST
        if is_reply:
            return TraceState.FAIL_REPLY
        return TraceState.FAIL_REQUEST
