# src/skyweaver/core/bus/monitor.py

from enum import Enum, auto
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from rich.console import Console
from rich.text import Text

from skyweaver.core.bus.message_context import MessageContext
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.messages.lifecycle_message import (
    ServiceReady,
    NotifyJoinMessage,
    DependenciesSatisfied,
)

from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.topics_enum import TopicsEnum

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
        

    def on_lifecycle_event(self, topic: TopicsEnum, message: BaseMessage, context: MessageContext):
        
        if isinstance(message, ServiceReady):
            self._print_service_ready(message, context)
            return
        
        if isinstance(message, NotifyJoinMessage):
            self._print_notify_join(message, context)
            return
        
        if isinstance(message, DependenciesSatisfied):
            self._print_dependencies_satisfied(message, context)
            return


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

    def _print_service_ready(self, message, context):

        line = Text()

        # Status dot (sempre verde)
        line.append("● ", style="green")

        # Topic
        line.append(f"{TopicsEnum.LIFECYCLE.name:<12} ", style="cyan")

        # Placeholder de trace (fixa alinhamento)
        line.append(f"{'(ready)':<14} ", style="grey50")

        # Actor
        origin_id = context.from_id
        origin = self._resolve_id(origin_id)
        line.append(origin)

        # Textual hint (depends on reserved ID)
        if origin_id in (r.value for r in ReservedIDs):
            line.append(" is alive", style="bold green")
        else:
            line.append(" ready", style="bold green")

        self.console.print(line)

    def _print_notify_join(self, message: NotifyJoinMessage, context: MessageContext):
        line = Text()

        # Status dot
        line.append("● ", style="green")

        # Topic
        line.append(f"{TopicsEnum.LIFECYCLE.name:<12} ", style="cyan")

        # Lifecycle state
        deps = message.dependencies or []
        n = len(deps)

        state = "(waiting)" if n > 0 else "(ready)"
        line.append(f"{state:<14} ", style="grey50")

        # Actor
        origin = self._resolve_id(context.from_id)
        line.append(origin)
        line.append(" joined", style="bold cyan")
        # Dependency info
        if n > 0:
            first = deps[0].__name__
            line.append(
                f" Dependencies: {first} + {n - 1}",
                style="dim",
            )

        self.console.print(line)

    def _print_dependencies_satisfied(
        self,
        message: DependenciesSatisfied,
        context: MessageContext,
    ):
        pid = context.from_id
        deps = message.parcel_types

        if not deps:
            return

        deps_list = sorted(deps, key=lambda t: t.__name__)

        line = Text()

        # Status dot
        line.append("● ", style="green")

        # Topic
        line.append(f"{TopicsEnum.LIFECYCLE.name:<12} ", style="cyan")

        # State label
        line.append(f"{'(waiting)':<14} ", style="grey50")

        # Actor
        origin = self._resolve_id(pid)
        line.append(origin)
        line.append(" dependencies satisfied ", style="bold green")

        # Dependency info
        first = deps_list[0].__name__
        extra = f" (+{len(deps_list) - 1})" if len(deps_list) > 1 else ""
        line.append(first + extra, style="grey50")

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
