import logging
from typing import Dict, Optional
import threading

from skyweaver.core.bus.observability.handler import RichTraceHandler
from skyweaver.core.bus.observability.renderer import EventRenderer
from skyweaver.core.bus.broker import Broker
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.message_handler import MessageHandler
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.observability.monitor import Monitor
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.publisher_manager import (
    Publisher,
    PublisherID,
    PublisherManager,
)


class MessageHub:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._brokers: Dict[TopicsEnum, Broker] = {}
        self.publisher_manager = PublisherManager()

        logger = logging.getLogger("skyweaver.bus")
        self.monitor = Monitor(logger)

        renderer = EventRenderer(self.publisher_manager)
        handler = RichTraceHandler(renderer)

        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if not any(
            isinstance(existing, RichTraceHandler) for existing in logger.handlers
        ):
            logger.addHandler(handler)

    # ==========================================================
    # Publisher Management
    # - Register: valid ID generation
    # - Unregister: cleanup topics and send termination messages
    # ==========================================================

    def register_publisher(self, owner: object) -> PublisherID:
        with self._lock:
            pid = self.publisher_manager.add_publisher(owner)
            return pid

    def _unregister_publisher(self, publisher_id: PublisherID):
        """Unregister a publisher and send termination messages to all its topics."""
        with self._lock:
            self.publisher_manager.remove(publisher_id)

    def get_publisher(self, publisher_id: PublisherID) -> Optional[Publisher]:
        return self.publisher_manager.get(publisher_id)

    # ==========================================================
    # Broker Management
    # Subscribe / Unsubscribe / Publish
    # ==========================================================

    def subscribe(
        self, topic: TopicsEnum, publisher_id: PublisherID, handler: MessageHandler
    ) -> None:
        """Subscribe to a specific topic."""
        self._get_broker(topic).subscribe(topic, publisher_id, handler)

    def unsubscribe(self, topic: TopicsEnum, publisher_id: PublisherID) -> None:
        """Unsubscribe from a specific topic."""
        self._get_broker(topic).unsubscribe(topic, publisher_id)

    def unregister_owner(self, publisher_id: PublisherID) -> None:
        for topic, broker in self._brokers.items():
            broker.unsubscribe(topic, publisher_id)

        self._unregister_publisher(publisher_id)

    def publish(
        self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext
    ) -> bool:
        """
        deffer-flush
        """

        if self.monitor:
            self.monitor.on_emit(
                topic=topic,
                message=message,
                context=message_context,
            )

        broker = self._brokers.get(topic)

        if not broker:
            return False

        delivered = broker.publish(topic, message, message_context)

        if self.monitor:
            self.monitor.on_deliver(
                context=message_context,
                delivered=delivered,
            )

        message_context.flush()

        return delivered

    def _get_broker(self, topic: TopicsEnum) -> Broker:
        """Get or create a broker for a specific topic."""
        return self._brokers.setdefault(topic, Broker())
