# src/skyweaver/core/bus/monitor.py


import logging
from typing import Optional


from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.observability.trace import TraceEvent, TraceManager
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.base_message import BaseMessage


class Monitor:

    def __init__(self, logger: logging.Logger):

        self.trace_manager = TraceManager()
        self.logger = logger

    def on_emit(
        self,
        *,
        topic: TopicsEnum,
        message: BaseMessage,
        context: MessageContext,
    ):

        self.trace_manager.track(topic, message, context)

    def on_deliver(
        self,
        *,
        context: MessageContext,
        delivered: bool,
    ):

        event: Optional[TraceEvent] = self.trace_manager.close_track(context, delivered)

        if event is not None:
            self.logger.debug("trace-event", extra={"event": event})
