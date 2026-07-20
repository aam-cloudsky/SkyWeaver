from typing import Dict, cast

from rich.console import Console
from rich.text import Text

from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.observability.trace import TraceEvent
from skyweaver.core.bus.protocol.validity_message import ValidityMessage
from skyweaver.core.bus.publisher_manager import (
    PublisherID,
    PublisherManager,
    PublisherReservedIDs,
)
from skyweaver.core.logistics.lifecycle import LifecycleState, LifecycleStateMessage


class EventRenderer:
    TRACE_WIDTH = 14

    RENDER_STYLE = {
        "OK_REQUEST": {"arrow": " → ", "style": "dim"},
        "OK_REPLY": {"arrow": " ← ", "style": "cyan"},
        "FAIL_REQUEST": {"arrow": " -x ", "style": "red"},
        "FAIL_REPLY": {"arrow": " x- ", "style": "red"},
        "TIMEOUT": {"arrow": " ↯ ", "style": "bold yellow"},
        "REROUTE_REQUEST": {"arrow": " ≠> ", "style": "cyan"},
        "REROUTE_REPLY": {"arrow": " <≠ ", "style": "cyan"},
        "UNKNOWN": {"arrow": " ? ", "style": "red"},
    }

    # ==========================================================
    # Initialization
    # ==========================================================

    def __init__(self, publisher_manager: PublisherManager):
        self.console = Console()
        self.publisher_manager = publisher_manager

        self.topic_width = max(len(t.name) for t in TopicsEnum) + 2

        self._topic_renderers = {
            TopicsEnum.LIFECYCLE: self._render_lifecycle,
            TopicsEnum.VALIDITY: self._render_validity,
        }

    # ==========================================================
    # Entry Point
    # ==========================================================

    def render_trace(self, trace_event: TraceEvent):

        topic = trace_event.trace.topic

        renderer = self._topic_renderers.get(topic, self._render_default)

        renderer(trace_event)

    # ==========================================================
    # Default Trace Renderer
    # ==========================================================

    def _render_default(self, trace_event: TraceEvent):

        trace = trace_event.trace
        state = trace_event.state
        ok = trace.delivered

        line = Text()

        # Status dot
        line.append("● ", style="green" if ok else "red")

        # Topic
        line.append(f"{trace.topic.name:<{self.topic_width}} ", style="cyan")

        # Trace ID
        trace_id = trace.reply_to or trace.trace_id
        short = trace_id.short(6)
        trace_txt = f"({short})"

        trace_style = "grey50" if not trace.reply_to else "cyan"
        line.append(f"{trace_txt:<{self.TRACE_WIDTH}} ", style=trace_style)

        render = self.RENDER_STYLE.get(state.name, self.RENDER_STYLE["UNKNOWN"])

        # Direction
        if trace.reply_to:
            line.append(self._resolve_id(trace.target))
            line.append(render["arrow"], style=render["style"])
            line.append(self._resolve_id(trace.origin))
        else:
            line.append(self._resolve_id(trace.origin))
            line.append(render["arrow"], style=render["style"])
            line.append(self._resolve_id(trace.target))

        self.console.print(line)

    # ==========================================================
    # Lifecycle Renderer
    # ==========================================================

    def _render_lifecycle(self, trace_event: TraceEvent):

        trace = trace_event.trace
        message = trace.message

        if not isinstance(message, LifecycleStateMessage):
            self._render_default(trace_event)
            return

        line = Text()

        origin = self._resolve_id(trace.origin)
        line.append(origin)

        state = message.state

        if state == LifecycleState.JOINED:
            line.append(" joined", style="bold cyan")

        elif state == LifecycleState.SYNCED:
            line.append(" synced", style="bold green")

        elif state == LifecycleState.READY:
            line.append(" ready", style="bold green")

        elif state == LifecycleState.ACTIVE:
            line.append(" active", style="bold green")

        elif state == LifecycleState.BUSY:
            line.append(" busy", style="bold yellow")

        elif state == LifecycleState.ERROR:
            line.append(" error", style="bold red")

        self.console.print(line)

    # ==========================================================
    # Validity Renderer
    # ==========================================================

    def _render_validity(self, trace_event: TraceEvent):

        trace = trace_event.trace
        message = trace.message

        if not isinstance(message, ValidityMessage):
            self._render_default(trace_event)
            return

        validity_message = cast(ValidityMessage, message)

        became_valid = validity_message.validity_transition.became_valid
        became_invalid = validity_message.validity_transition.became_invalid
        source_id = validity_message.validity_source_id

        line = Text()

        if became_valid:
            line.append("+", style="green")
            line.append(
                ", ".join(p.__name__ for p in became_valid),
                style="bold green",
            )

        if became_invalid:
            if became_valid:
                line.append("  ")

            line.append("-", style="red")
            line.append(
                ", ".join(p.__name__ for p in became_invalid),
                style="red",
            )

        line.append(" ∵ ", style="grey50")
        line.append(str(self._resolve_id(source_id)), style="grey50")

        self.console.print(line)

    # ==========================================================
    # Publisher Resolution
    # ==========================================================

    def _resolve_id(self, pid: PublisherID) -> Text:

        # Normalize Enum → int → PublisherID
        if isinstance(pid, PublisherReservedIDs):
            pid = PublisherID(pid.value)

        # Reserved IDs
        for r in PublisherReservedIDs:
            if int(pid) == r.value:
                t = Text(r.name, style="magenta")
                t.append(f"#p:{int(pid)}", style="grey50")
                return t

        # Dynamic publishers
        info = self.publisher_manager.get(pid)

        if info:
            t = Text(info.label, style="yellow")
            t.append(f"#p:{int(pid)}", style="grey50")
            return t

        # Fallback
        t = Text("Publisher", style="red")
        t.append(f"#p:{int(pid)}", style="grey50")
        return t
