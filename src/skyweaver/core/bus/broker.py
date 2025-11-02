import threading
from typing import Callable, Dict, List

from skyweaver.core.bus.message_context import MessageContext
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
        self._subscribers: Dict[TopicsEnum, Dict[int, Callable[[Dict, MessageContext], None]]] = {}


    def subscribe(self, topic: TopicsEnum, publisher_id: int, subscriber: Callable[[Dict, MessageContext], None]) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = {}

            self._subscribers[topic][publisher_id] = subscriber


    def unsubscribe(self, topic: TopicsEnum, publisher_id: int) -> None:
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic].pop(publisher_id, None)



    def publish(self, topic: TopicsEnum, message: Dict, message_context: MessageContext) -> None:
        
        
        to_id:int = message_context.to_id
        subscribers = self._subscribers.get(topic, {})
        
        if to_id == ReservedIDs.BROADCAST.value:
            for sid, subscriber in subscribers.items():
                if sid in message_context.exclude_ids:
                    continue
                if sid == message_context.from_id:
                    continue  # still skip self
                subscriber(message, message_context)


        elif to_id in subscribers:
            try:
                subscribers[to_id](message, message_context)
            except Exception as e:
                print(f"[WARN] Subscriber {to_id} failed: {e}")



