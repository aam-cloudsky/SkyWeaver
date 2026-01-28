

from dataclasses import dataclass, field
from enum import auto
from typing import Dict, Callable, List, Optional, Tuple
import threading

from skyweaver.core.bus.runtime.broker import Broker
from skyweaver.core.bus.runtime.id_manager import IDManager
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.message_handler import MessageHandler
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.observability.monitor import EventMonitor
from skyweaver.core.bus.enums.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.enums.topics_enum import TopicsEnum





class MessageHub:
    _thread_local_data = threading.local()

    def __new__(cls):
        if not hasattr(cls._thread_local_data, '_instance'):
            cls._thread_local_data._instance = super(MessageHub, cls).__new__(cls)
            cls._thread_local_data._instance._initialize()
            #cls._ensure_depot_registered()
            print("[MessageHub] Initialized thread-local singleton instance.")
            print(f"[MessageHub] Please, ensure Depot is alive and subscribed.")
            # now, you have to instantiate Depot somewhere else!
        return cls._thread_local_data._instance
            
    def _initialize(self) -> None:
        """Initialize attributes for the instance."""
        self._lock = threading.Lock()
        
        self._id_manager = IDManager()
        self._brokers: Dict[TopicsEnum, Broker] = {}


        self.monitor = EventMonitor()
        self.enable_monitoring()




    def enable_monitoring(self, value: bool = True):
        self.monitor.set_enabled(value)


    #@staticmethod
    #def _ensure_depot_registered():
    #    """Guarantee Depot is instantiated and subscribed."""
    #    try:
            
    #        from skyweaver.core.logistics.depot import Depot
            #Depot()  # triggers __init__ and subscription once
    #    except Exception as e:
    #        print(f"[WARN] Could not auto-register Depot: {e}")

    # ==========================================================
    # Publisher Management
    # - Register: valid ID generation
    # - Unregister: cleanup topics and send termination messages
    # ==========================================================

    def register_publisher(self, owner: object) -> int:
        with self._lock:
            pid = self._id_manager.get_or_create_id(owner)
            self.monitor.add_publisher(publisher_id=pid, owner=owner)
            return pid


    def _unregister_publisher(self, publisher_id: int):
        """Unregister a publisher and send termination messages to all its topics."""
        with self._lock:
            self._id_manager.release_id(publisher_id)

    

    # ==========================================================
    # Broker Management
    # Subscribe / Unsubscribe / Publish
    # ==========================================================

    def subscribe(self, topic: TopicsEnum, publisher_id: int, handler: MessageHandler) -> None:
        """Subscribe to a specific topic."""
        self._get_broker(topic).subscribe(topic, publisher_id, handler)


    def unsubscribe(self, topic: TopicsEnum, publisher_id: int) -> None:
        """Unsubscribe from a specific topic."""
        self._get_broker(topic).unsubscribe(topic, publisher_id)

    def publish(self, topic: TopicsEnum, message: BaseMessage, message_context: MessageContext) -> bool:
            
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
            

        self.monitor.on_deliver(
                topic=topic,
                message=message,
                context=message_context,
                delivered=delivered,
            )
        
        message_context.flush()

        return delivered
        


    def _get_broker(self, topic: TopicsEnum) -> Broker:
        """Get or create a broker for a specific topic."""
        return self._brokers.setdefault(topic, Broker())
   

    def create_message_context(self, from_id: int, to_id: Optional[int] = None) -> MessageContext:
        """Create a MessageContext for publishing messages."""

        if to_id is None:
            to_id = ReservedIDs.BROADCAST.value
        return MessageContext(from_id=from_id, to_id=to_id)
    