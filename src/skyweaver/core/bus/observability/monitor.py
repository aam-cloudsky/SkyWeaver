# src/skyweaver/core/bus/monitor.py

from enum import Enum, auto
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from rich.console import Console
from rich.text import Text

from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.base_message import BaseMessage


from skyweaver.core.bus.enums.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.logistics.lifecycle import LifecycleState, LifecycleStateMessage

#TODO: Refactor monitor to have separate classes for rendering and trace management

# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class PublisherInfo:
    pid: int
    cls: str
    module: str
    label: str


@dataclass
class TraceRecord:
    trace_id: UUID
    reply_to: Optional[UUID]

    topic: TopicsEnum
    origin: int
    target: int
    message: str

    delivered: bool = False


class TraceState(Enum):
    OK_REQUEST = auto()
    OK_REPLY = auto()
    FAIL_REQUEST = auto()
    FAIL_REPLY = auto()
    TIMEOUT = auto()
    REROUTE_REQUEST = auto()
    REROUTE_REPLY = auto()


class TraceManager():
    #TODO: IMPLEMENT
    def resolve_trace_state(self, trace: TraceRecord) -> TraceState:
        if trace.delivered and trace.reply_to:
            return TraceState.OK_REPLY
        if trace.delivered and not trace.reply_to:
            return TraceState.OK_REQUEST
        if not trace.delivered and trace.reply_to:
            return TraceState.FAIL_REPLY
        if not trace.delivered and not trace.reply_to:
            return TraceState.FAIL_REQUEST
        return TraceState.FAIL_REQUEST

# ---------------------------------------------------------------------
# Event Monitor
# ---------------------------------------------------------------------

class EventMonitor:

    def __init__(self):
        self.enabled: bool = False
        self.publisher_registry: Dict[int, PublisherInfo] = {}
        self._traces: Dict[UUID, TraceRecord] = {}
        self.renderer = EventRenderer(self.publisher_registry)


    # ------------------------------------------------------------------
    # Publisher registry
    # ------------------------------------------------------------------

    def add_publisher(self, publisher_id: int, owner: object):
        self.publisher_registry[publisher_id] = PublisherInfo(
            pid=publisher_id,
            cls=owner.__class__.__name__,
            module=owner.__class__.__module__,
            label=owner.__class__.__name__,
        )

    def set_enabled(self, value: bool):
        self.enabled = value

    def _gen_trace(self, topic: TopicsEnum,
                   message: BaseMessage,
                   context: MessageContext) -> TraceRecord:
        

        return TraceRecord(
            trace_id=context.trace_id,
            reply_to=context.reply_to,
            topic=topic,
            origin=context.from_id,
            target=context.to_id,
            message=message.__class__.__name__,
            delivered=False,
        )

    # ------------------------------------------------------------------
    # Trace Events
    # ------------------------------------------------------------------

    def on_emit(
        self,
        *,
        topic: TopicsEnum,
        message: BaseMessage,
        context: MessageContext,
    ):
        if not self.enabled:
            return
        
        if topic == TopicsEnum.LIFECYCLE:
            self.renderer.on_lifecycle_event(topic, message, context)
            return

        # SEMPRE cria um trace novo
        self._traces[context.trace_id] = self._gen_trace(topic, message, context)

    def on_deliver(
        self,
        *,
        topic: TopicsEnum,
        message: BaseMessage,
        context: MessageContext,
        delivered: bool,
    ):

        if not self.enabled:
            return

        trace = self._traces.get(context.trace_id)
        if trace:
            trace.delivered = delivered
            self.renderer.on_trace_delivered(trace)
            self._traces.pop(trace.trace_id, None)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------


class EventRenderer:
    TOPIC_WIDTH = 12
    TRACE_WIDTH = 14   # "(-> XXXXXXXX)" ou "(<- XXXXXXXX)"
    REPLY_COL_WIDTH = 14   # "(↩ XXXXXXXX) "

    RENDER_STYLE = {
        "OK-REQUEST":    {"arrow": " → ", "style": "dim"},
        "OK-REPLY":    {"arrow": " ← ", "style": "cyan"},
        "FAIL-REQUEST":  {"arrow": " -x ", "style": "red"},
        "FAIL-REPLY":  {"arrow": " x- ", "style": "red"},
        "TIMEOUT": {"arrow": " ↯ ", "style": "bold yellow"},
        "REROUTE-REQUEST": {"arrow": " ≠> ", "style": "cyan"},
        "REROUTE-REPLY": {"arrow": " <≠ ", "style": "cyan"},
        "DEGRADED": {"arrow": " ⚠ ", "style": "yellow"},
        "UNKNOWN": {"arrow": " ? ", "style": "red"},
    }

    def __init__(self, publisher_registry: Dict[int, PublisherInfo]):
        self.console = Console()
        self.publisher_registry: Dict[int, PublisherInfo] = publisher_registry




    def on_trace_delivered(self, trace: TraceRecord):
        self._print_trace(trace)
        
    def on_lifecycle_event(
        self,
        topic: TopicsEnum,
        message: BaseMessage,
        context: MessageContext,
    ):
        if not isinstance(message, LifecycleStateMessage):
            return

        self._print_lifecycle_state(message, context)

    def _print_lifecycle_state(
        self,
        message: LifecycleStateMessage,
        context: MessageContext,
    ):
        line = Text()

        # Status dot (verde exceto ERROR)
        style = "red" if message.state == LifecycleState.ERROR else "green"
        line.append("● ", style=style)

        # Topic
        line.append(f"{TopicsEnum.LIFECYCLE.name:<12} ", style="cyan")

        # State label (fixo, alinhado)
        #state_label = f"({message.state.name.lower()})"
        state_label = ""
        line.append(f"{state_label:<14} ", style="grey50")

        # Actor
        origin = self._resolve_id(context.from_id)
        line.append(origin)

        # Optional semantic hint
        if message.state == LifecycleState.JOINED:
            line.append(" joined", style="bold cyan")
        elif message.state == LifecycleState.READY:
            line.append(" ready", style="bold green")
        elif message.state == LifecycleState.ACTIVE:
            line.append(" active", style="bold green")
        elif message.state == LifecycleState.BUSY:
            line.append(" busy", style="bold yellow")
        elif message.state == LifecycleState.ERROR:
            line.append(" error", style="bold red")

        self.console.print(line)


    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _trace_state(self, trace: TraceRecord) -> str:
        if trace.delivered and trace.reply_to:
            return "OK-REPLY"
        elif trace.delivered and not trace.reply_to:
            return "OK-REQUEST"
        elif not trace.delivered and trace.reply_to:
            return "FAIL-REPLY"
        elif not trace.delivered and not trace.reply_to:
            return "FAIL-REQUEST"
        return "UNKNOWN"

    def _print_trace(self, trace: TraceRecord):

        state = self._trace_state(trace)
        ok = trace.delivered

        line = Text()

        # ------------------------------------------------------------------
        # Status dot (single source of truth)
        # ------------------------------------------------------------------
        line.append("● ", style="green" if ok else "red")

        # ------------------------------------------------------------------
        # Topic (fixed width)
        # ------------------------------------------------------------------
        line.append(f"{trace.topic.name:<12} ", style="cyan")

        # ------------------------------------------------------------------
        # Trace ID (fixed width, same position always)
        # ------------------------------------------------------------------
        trace_id = trace.reply_to or trace.trace_id
        short = str(trace_id)[:8]
        trace_txt = f"({short})"
        trace_style = "grey50" if not trace.reply_to else "cyan"
        line.append(f"{trace_txt:<14} ", style=trace_style)


        # ------------------------------------------------------------------
        # Direction + actors
        # Outpost always on the left
        # ------------------------------------------------------------------

        if trace.reply_to:
            # Reply: Outpost ← Depot
            line.append(self._resolve_id(trace.target))

            render = self.RENDER_STYLE[state]
            line.append(render["arrow"], style=render["style"])

            line.append(self._resolve_id(trace.origin))

        else:
            # Request: Outpost → Depot
            line.append(self._resolve_id(trace.origin))

            render = self.RENDER_STYLE[state]
            line.append(render["arrow"], style=render["style"])

            line.append(self._resolve_id(trace.target))


        self.console.print(line)

    def _resolve_id(self, pid: int) -> Text:
        for r in ReservedIDs:
            if r.value == pid:
                t = Text(r.name, style="magenta")
                t.append(f"#{pid}", style="grey50")
                return t

        info = self.publisher_registry.get(pid)
        if info:
            t = Text(info.label, style="yellow")
            t.append(f"#{pid}", style="grey50")
            return t

        t = Text("UNKNOWN", style="red")
        t.append(f"#{pid}", style="grey50")
        return t
