import logging
from typing import Optional

from skyweaver.core.bus.observability.renderer import EventRenderer
from skyweaver.core.bus.observability.trace import TraceEvent


class RichTraceHandler(logging.Handler):

    def __init__(self, renderer: EventRenderer):
        super().__init__()
        self.renderer = renderer

    def emit(self, record: logging.LogRecord):

        event: Optional[TraceEvent] = getattr(record, "event", None)

        if event is None:
            return

        self.renderer.render_trace(event)
