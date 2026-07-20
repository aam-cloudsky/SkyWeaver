import threading
from typing import Dict

from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.message_handler import MessageHandler
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.publisher_manager import (
    PublisherID,
    PublisherReservedIDs,
)


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
        self._subscribers: Dict[TopicsEnum, Dict[PublisherID, MessageHandler]] = {}

    def subscribe(
        self, topic: TopicsEnum, publisher_id: PublisherID, handler: MessageHandler
    ) -> None:
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = {}

            self._subscribers[topic][publisher_id] = handler

    def unsubscribe(self, topic: TopicsEnum, publisher_id: PublisherID) -> None:
        with self._lock:
            if topic in self._subscribers:
                self._subscribers[topic].pop(publisher_id, None)

    def publish(
        self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext
    ) -> bool:

        to_id: PublisherID = message_context.to_id
        subscribers = self._subscribers.get(topic, {})

        delivered = False

        if to_id == PublisherReservedIDs.BROADCAST:
            for sid, handler in subscribers.items():
                if sid in message_context.exclude_ids:
                    continue
                if sid == message_context.from_id:
                    continue  # still skip self

                handler(message, message_context)
                delivered = True

        elif to_id in subscribers:
            try:
                subscribers[to_id](message, message_context)
                delivered = True
            except Exception as e:
                # print(f"[BROKER][WARN] Subscriber {to_id} failed: {e}")
                delivered = False
                raise

        return delivered
