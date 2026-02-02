from typing import Any, Callable, Dict, Optional, Type, Set, cast
from uuid import UUID
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.message_handler import MessageHandler
from skyweaver.core.bus.runtime.hub import MessageHub
from skyweaver.core.bus.enums.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.logistics.depot_messages import DepotGet, DepotSet, DepotUpdate
from skyweaver.core.logistics.lifecycle import LifecycleState, LifecycleStateMessage
from skyweaver.core.logistics.parcel import Parcel


class Port:
    def __init__(
        self,
        topic: TopicsEnum,
        owner: object,
        on_arrive: Callable[[BaseMessage, MessageContext], Any] = lambda msg, ctx: None,
        on_end_arrive: Callable[[Optional[Any]], Any] = lambda result: None,
    ):
        
        self.topic: TopicsEnum = topic
        self._on_arrive = on_arrive
        self._on_end_arrive = on_end_arrive

        self._message_hub = MessageHub()
        self._publisher_id = self._message_hub.register_publisher(owner=owner)

        handler = MessageHandler(accept=self._action, react=self._reaction)
        self._message_hub.subscribe(
            topic=self.topic,
            publisher_id=self._publisher_id,
            handler=handler,
        )

    def send(self, message: BaseMessage, to_id: int = ReservedIDs.DEPOT.value, reply_to: Optional[UUID] = None):

        publisher_type = self._message_hub.resolve_owner_type(self._publisher_id)

        if publisher_type is None:
            raise RuntimeError(
                "Invariant violation: Port has publisher_id but no owner_type registered"
            )

        self._message_hub.publish(
            topic=self.topic,
            message=message,
            message_context=MessageContext(
                from_id=self._publisher_id,
                to_id=to_id,
                publisher_type=publisher_type,
                reply_to=reply_to,
            ),
        )

    def _action(self, message: BaseMessage, context: MessageContext) -> Any:
        if self._should_ignore(message, context):
            return
        return self._on_arrive(message, context)

    def _reaction(self, result: Optional[Any]) -> None:
        self._on_end_arrive(result)

    def _should_ignore(self, message: BaseMessage, context: MessageContext) -> bool:
        if context.from_id == self._publisher_id:
            return True

        return False
