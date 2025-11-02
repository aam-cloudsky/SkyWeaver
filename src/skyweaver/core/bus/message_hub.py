

from dataclasses import field
from enum import auto
from typing import Dict, Callable, List, Optional
import threading

from skyweaver.core.bus.broker import Broker
from skyweaver.core.bus.message_context import MessageContext
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.topics_enum import TopicsEnum

class MessageHub:
    _thread_local_data = threading.local()

    def __new__(cls):
        if not hasattr(cls._thread_local_data, '_instance'):
            cls._thread_local_data._instance = super(MessageHub, cls).__new__(cls)
            cls._thread_local_data._instance._initialize()
            cls._ensure_airspace_state_registered()
        return cls._thread_local_data._instance
            
    def _initialize(self) -> None:
        """Initialize attributes for the instance."""
        self._lock = threading.Lock()
        
        self._brokers: Dict[TopicsEnum, Broker] = {}
        self._publishers_dict: Dict[int, List[TopicsEnum]] = {}

        SYSTEM_ID_OFFSET: int = max(r.value for r in ReservedIDs) + 10
        self.last_publisher_id_generated: int = SYSTEM_ID_OFFSET

        

        

    @staticmethod
    def _ensure_airspace_state_registered():
        """Guarantee AirspaceState is instantiated and subscribed."""
        try:
            from skyweaver.airspace.airspace_state import AirspaceState
            AirspaceState()  # triggers __init__ and subscription once
        except Exception as e:
            print(f"[WARN] Could not auto-register AirspaceState: {e}")

    # ==========================================================
    # Publisher Management
    # - Register: valid ID generation
    # - Unregister: cleanup topics and send termination messages
    # ==========================================================

    def register_publisher(self) -> int:
        """Register a new publisher and generate a unique ID."""
        with self._lock:
            self.last_publisher_id_generated += 1
            return self.last_publisher_id_generated

    def _unregister_publisher(self, publisher_id: int):
        """Unregister a publisher and send termination messages to all its topics."""

        topics = self._publishers_dict.get(publisher_id, []).copy()
        message_context = self.create_message_context(from_id=publisher_id)

        for topic in topics:
            self.publish(topic=topic,
                         message={"termination": True},
                         message_context=message_context)

        if publisher_id in self._publishers_dict:
            del self._publishers_dict[publisher_id]

    def _register_publisher_topic(self, topic: TopicsEnum, publisher_id: int):
        """Register a publisher for a specific topic."""
        if publisher_id not in self._publishers_dict:
            self._publishers_dict[publisher_id] = []

        if topic not in self._publishers_dict[publisher_id]:
            self._publishers_dict[publisher_id].append(topic)

    def _unregister_publisher_topic(self, topic: TopicsEnum, publisher_id: int):
        """Unregister a publisher and send termination messages to all its topics."""

        message_context = self.create_message_context(from_id=publisher_id)

        self.publish(topic=topic, message={
                     "termination": True}, message_context=message_context)

        # Remove the topic from the list of topics for the publisher
        if publisher_id in self._publishers_dict:
            topics = self._publishers_dict[publisher_id]
            if topic in topics:
                topics.remove(topic)

    # ==========================================================
    # Broker Management
    # Subscribe / Unsubscribe / Publish
    # ==========================================================



    def subscribe(self, topic: TopicsEnum, publisher_id: int, subscriber: Callable[[Dict, MessageContext], None]) -> None:
        """Subscribe to a specific topic."""
        self._get_broker(topic).subscribe(topic, publisher_id, subscriber)




    def unsubscribe(self, topic: TopicsEnum, publisher_id: int) -> None:
        """Unsubscribe from a specific topic."""
        self._get_broker(topic).unsubscribe(topic, publisher_id)

    def publish(self, topic: TopicsEnum, message: Dict, message_context: MessageContext) -> None:
        broker = self._brokers.get(topic)
        if not broker:
            print(f"[WARN] No subscribers for topic {topic.name}")
            return

        self._register_publisher_topic(topic, message_context.from_id)
        broker.publish(topic, message, message_context)


    def _get_broker(self, topic: TopicsEnum) -> Broker:
        """Get or create a broker for a specific topic."""
        return self._brokers.setdefault(topic, Broker())

   

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


    

