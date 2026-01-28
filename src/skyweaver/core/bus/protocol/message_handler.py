from typing import Any, Callable

from skyweaver.core.bus.protocol.message_context import MessageContext
from skyweaver.core.bus.protocol.base_message import BaseMessage


class MessageHandler:
    def __init__(self, accept: Callable[[BaseMessage, MessageContext], Any], react: Callable[[Any], None]):
        self._accept = accept
        self._react = react

    def __call__(self, message: BaseMessage, context: MessageContext):
        #if context._closed:
        #    raise RuntimeError("Context already closed")

        result = self._accept(message, context)
        context.close_transaction(result)
        context.defer(self._react, result)
