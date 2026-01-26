import threading
from typing import Callable, Dict, List, Optional

from skyweaver.core.bus.message_context import MessageContext
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.monitor import EventMonitor
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.topics_enum import TopicsEnum



class Broker:
    """
    Routes messages between publishers and subscribers for a specific topic.

    - Subscribers are identified by their unique `publisher_id`.
    - Each topic has its own dictionary of subscribers.
    - When a message is published:
        * If `to_id == BROADCAST`, all subscribers receive it.
        * Otherwise, only the matching subscriber is triggered.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: Dict[TopicsEnum, Dict[int, Callable[[
            BaseMessage, MessageContext], None]]] = {}

        self._post_subscribers: Dict[TopicsEnum, Dict[int, Callable[[
            BaseMessage, MessageContext, bool], None]]] = {}
        
    def subscribe(self, topic: TopicsEnum, publisher_id: int, subscriber: Callable[[BaseMessage, MessageContext], None], post_subscriber: Optional[Callable[[BaseMessage, MessageContext, bool], None]] = None) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = {}
                self._post_subscribers[topic] = {}

            self._subscribers[topic][publisher_id] = subscriber

            if post_subscriber:
                self._post_subscribers[topic][publisher_id] = post_subscriber


    def unsubscribe(self, topic: TopicsEnum, publisher_id: int) -> None:
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic].pop(publisher_id, None)
                self._post_subscribers[topic].pop(publisher_id, None)

    def publish(self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext) -> bool:
        
        
        to_id:int = message_context.to_id
        subscribers = self._subscribers.get(topic, {})

        delivered = False
        
        if to_id == ReservedIDs.BROADCAST.value:
            for sid, subscriber in subscribers.items():
                if sid in message_context.exclude_ids:
                    continue
                if sid == message_context.from_id:
                    continue  # still skip self
                subscriber(message, message_context)
                delivered = True

        elif to_id in subscribers:
            try:
                subscribers[to_id](message, message_context)
                delivered = True
            except Exception as e:
                #print(f"[BROKER][WARN] Subscriber {to_id} failed: {e}")
                delivered = False

        return delivered


    def post_publish(self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext, delivered: bool) -> None:
        post_subscribers = self._post_subscribers.get(topic, {})

        sender_id = message_context.from_id
        receiver_id = message_context.to_id

        
        if sender_id in post_subscribers:
            post_subscribers[sender_id](message, message_context, delivered)

        if receiver_id in post_subscribers and receiver_id != sender_id:
            post_subscribers[receiver_id](message, message_context, delivered)

        

    def _format_id(self, pid: int) -> str:
        for r in ReservedIDs:
            if r.value == pid:
                return f"{r.name} (id={pid})"
        return str(pid)
