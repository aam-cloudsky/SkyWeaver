# src/skyweaver/core/bus/monitor.py

from dataclasses import dataclass
from typing import Dict, Optional
from uuid import UUID

from rich.console import Console
from rich.text import Text

from skyweaver.core.bus.message_context import MessageContext
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.messages.lifecycle_message import ServiceReady
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.topics_enum import TopicsEnum


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
    failed: bool = False


# ---------------------------------------------------------------------
# Event Monitor
# ---------------------------------------------------------------------

class EventMonitor:
    """
    Reactive, trace-aware monitor.

    Rules:
    - on_emit creates trace
    - on_deliver closes trace
    - if target == DEPOT: wait for reply
    - otherwise: print immediately
    """
    TOPIC_WIDTH = 12
    TRACE_WIDTH = 14   # "(-> XXXXXXXX)" ou "(<- XXXXXXXX)"


    def __init__(self):
        self.enabled: bool = False
        self.publisher_registry: Dict[int, PublisherInfo] = {}
        self._traces: Dict[UUID, TraceRecord] = {}
        self.console = Console()
        self._pending_replies: Dict[UUID, TraceRecord] = {}
        self.REPLY_COL_WIDTH = 14   # "(↩ XXXXXXXX) "


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

    # ------------------------------------------------------------------
    # Trace lifecycle
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
        
        if isinstance(message, ServiceReady):
            self._print_service_ready(message, context)
            return


        # SEMPRE cria um trace novo
        self._traces[context.trace_id] = TraceRecord(
            trace_id=context.trace_id,
            reply_to=context.reply_to,
            topic=topic,
            origin=context.from_id,
            target=context.to_id,
            message=message.__class__.__name__,
            delivered=False,
            failed=False,
        )

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
        if not trace:
            return

        trace.delivered = delivered
        trace.failed = not delivered

        # 🔁 CASO 1: é um reply
        if trace.reply_to:
            # guarda o reply, NÃO imprime ainda
            self._pending_replies[trace.reply_to] = trace
            return

        # 📤 CASO 2: é request (Outpost → Depot)
        self._print_trace(trace)
        self._traces.pop(trace.trace_id, None)

        # 🔓 Se existe reply pendente, imprime agora
        reply = self._pending_replies.pop(trace.trace_id, None)
        if reply:
            self._print_trace(reply)
            self._traces.pop(reply.trace_id, None)




    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _print_trace(self, trace: TraceRecord):
        ok = trace.delivered and not trace.failed

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
            line.append(" ← ", style="bold cyan")
            line.append(self._resolve_id(trace.origin))
        else:
            # Request: Outpost → Depot
            line.append(self._resolve_id(trace.origin))
            line.append(" → ", style="dim")
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
            line.append(" joined", style="bold cyan")

        self.console.print(line)



    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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

