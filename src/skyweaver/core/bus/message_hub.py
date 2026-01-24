

from dataclasses import dataclass, field
from enum import auto
from typing import Dict, Callable, List, Optional
import threading

from skyweaver.core.bus.broker import Broker
from skyweaver.core.bus.message_context import MessageContext
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.messages.lifecycle_message import TerminationMessage
from skyweaver.core.bus.monitor import EventMonitor
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.topics_enum import TopicsEnum

class MessageHub:
    _thread_local_data = threading.local()

    def __new__(cls):
        if not hasattr(cls._thread_local_data, '_instance'):
            cls._thread_local_data._instance = super(MessageHub, cls).__new__(cls)
            cls._thread_local_data._instance._initialize()
            cls._ensure_depot_registered()
        return cls._thread_local_data._instance
            
    def _initialize(self) -> None:
        """Initialize attributes for the instance."""
        self._lock = threading.Lock()
        
        self._brokers: Dict[TopicsEnum, Broker] = {}
        self._publishers_dict: Dict[int, List[TopicsEnum]] = {}

        self.monitor = EventMonitor()
        self.enable_monitoring()

        SYSTEM_ID_OFFSET: int = max(r.value for r in ReservedIDs) + 10
        self.last_publisher_id_generated: int = SYSTEM_ID_OFFSET


    def enable_monitoring(self, value: bool = True):
        self.monitor.set_enabled(value)


    @staticmethod
    def _ensure_depot_registered():
        """Guarantee Depot is instantiated and subscribed."""
        try:
            
            from skyweaver.core.logistics.depot import Depot
            Depot()  # triggers __init__ and subscription once
        except Exception as e:
            print(f"[WARN] Could not auto-register Depot: {e}")

    # ==========================================================
    # Publisher Management
    # - Register: valid ID generation
    # - Unregister: cleanup topics and send termination messages
    # ==========================================================

    def register_publisher(self, owner: object) -> int:
        """Register a new publisher and generate a unique ID."""
        with self._lock:
            self.last_publisher_id_generated += 1
            pid = self.last_publisher_id_generated

            self.monitor.add_publisher(publisher_id=pid, owner=owner)
            
            return pid
        



    def _unregister_publisher(self, publisher_id: int):
        """Unregister a publisher and send termination messages to all its topics."""

        topics = self._publishers_dict.get(publisher_id, []).copy()
        message_context = self.create_message_context(from_id=publisher_id)

        for topic in topics:
            self._publish_termination(topic, message_context)

        if publisher_id in self._publishers_dict:
            del self._publishers_dict[publisher_id]

    def _unregister_publisher_topic(self, topic: TopicsEnum, publisher_id: int):
        """Unregister a publisher and send termination messages to all its topics."""

        message_context = self.create_message_context(from_id=publisher_id)

        self._publish_termination(topic, message_context)

        # Remove the topic from the list of topics for the publisher
        if publisher_id in self._publishers_dict:
            topics = self._publishers_dict[publisher_id]
            if topic in topics:
                topics.remove(topic)

    def _publish_termination(self, topic: TopicsEnum, message_context: MessageContext):
        """Publish a termination message to a specific topic."""
        self.publish(
            topic=topic,
            message=TerminationMessage(),
            message_context=message_context
        )

    def _register_publisher_topic(self, topic: TopicsEnum, publisher_id: int):
        """Register a publisher for a specific topic."""
        if publisher_id not in self._publishers_dict:
            self._publishers_dict[publisher_id] = []

        if topic not in self._publishers_dict[publisher_id]:
            self._publishers_dict[publisher_id].append(topic)

    

    # ==========================================================
    # Broker Management
    # Subscribe / Unsubscribe / Publish
    # ==========================================================


    def subscribe(self, topic: TopicsEnum, publisher_id: int, subscriber: Callable[[BaseMessage, MessageContext], None]) -> None:
        """Subscribe to a specific topic."""
        self._get_broker(topic).subscribe(topic, publisher_id, subscriber)




    def unsubscribe(self, topic: TopicsEnum, publisher_id: int) -> None:
        """Unsubscribe from a specific topic."""
        self._get_broker(topic).unsubscribe(topic, publisher_id)

    def publish(self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext) -> None:

        if self.monitor:
            self.monitor.on_emit(
                topic=topic,
                message=message,
                context=message_context,
            )

        broker = self._brokers.get(topic)
        if not broker:
            print(f"[MESSAGEHUB WARN] No subscribers for topic {topic.name}")
            return

        self._register_publisher_topic(topic, message_context.from_id)
        broker.publish(topic, message, message_context)


    def _get_broker(self, topic: TopicsEnum) -> Broker:
        """Get or create a broker for a specific topic."""
        return self._brokers.setdefault(topic, Broker(monitor=self.monitor))

   

    def create_message_context(self, from_id: int, to_id: Optional[int] = None) -> MessageContext:
        """Create a MessageContext for publishing messages."""

        if to_id is None:
            to_id = ReservedIDs.BROADCAST.value
        return MessageContext(from_id=from_id, to_id=to_id)
    
    # ==========================================================
    # Special cases
    # - Terminate: unregister publisher or specific topic
    # ==========================================================

    def terminate(self, publisher_id: int, topic: Optional[TopicsEnum] = None) -> None:
        if topic:
            # Terminate the specific topic
            self._unregister_publisher_topic(topic, publisher_id)
        else:
            # Terminate all topics for the publisher
            self._unregister_publisher(publisher_id)
