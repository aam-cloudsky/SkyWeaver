from typing import Any, Callable, Optional, Self

from skyweaver.core.bus.enums.topics_enum import TopicsEnum
from skyweaver.core.bus.hub import MessageHub
from skyweaver.core.bus.port import Port
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.identifier.identifier import BusId


class Bus:
    def __init__(self, hub: MessageHub) -> None:
        self._hub = hub
        self.identity = BusId(self.__class__.__name__)

    @classmethod
    def create(cls) -> Self:
        return cls(hub=MessageHub())

    def port(
        self,
        *,
        topic: TopicsEnum,
        owner: object,
        on_arrive: Callable[
            [BaseMessage, MessageContext],
            Any,
        ] = lambda message, context: None,
        on_end_arrive: Callable[
            [Optional[Any]],
            Any,
        ] = lambda result: None,
    ) -> Port:
        return Port(
            message_hub=self._hub,
            topic=topic,
            owner=owner,
            on_arrive=on_arrive,
            on_end_arrive=on_end_arrive,
        )
