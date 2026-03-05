import logging
from typing import Dict, Optional
import threading

from skyweaver.core.bus.observability.handler import RichTraceHandler
from skyweaver.core.bus.observability.renderer import EventRenderer
from skyweaver.core.bus.runtime.broker import Broker
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.message_handler import MessageHandler
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.observability.monitor import Monitor
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.runtime.publisher_manager import (
    Publisher,
    PublisherID,
    PublisherManager,
)


class MessageHub:
    _thread_local_data = threading.local()

    def __new__(cls):
        if not hasattr(cls._thread_local_data, "_instance"):
            cls._thread_local_data._instance = super(MessageHub, cls).__new__(cls)
            cls._thread_local_data._instance._initialize()
            # cls._ensure_depot_registered()
            print("[MessageHub] Initialized thread-local singleton instance.")
            print(f"[MessageHub] Please, ensure Depot is alive and subscribed.")
            # now, you have to instantiate Depot somewhere else!
        return cls._thread_local_data._instance

    def _initialize(self) -> None:
        """Initialize attributes for the instance."""
        self._lock = threading.Lock()
        self._brokers: Dict[TopicsEnum, Broker] = {}
        self.publisher_manager = PublisherManager()

        logger: logging.Logger = logging.getLogger("skyweaver.bus")
        self.monitor = Monitor(logger)

        renderer = EventRenderer(self.publisher_manager)
        handler = RichTraceHandler(renderer)

        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        if not any(isinstance(h, RichTraceHandler) for h in logger.handlers):
            logger.addHandler(handler)

    # @staticmethod
    # def _ensure_depot_registered():
    #    """Guarantee Depot is instantiated and subscribed."""
    #    try:

    #        from skyweaver.core.logistics.depot import Depot
    # Depot()  # triggers __init__ and subscription once
    #    except Exception as e:
    #        print(f"[WARN] Could not auto-register Depot: {e}")

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

    def publish(
        self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext
    ) -> bool:

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
