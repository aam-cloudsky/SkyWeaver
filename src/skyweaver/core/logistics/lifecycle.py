
# core/logistics/lifecycle.py

from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.core.bus.messages.lifecycle_message import ServiceReady, TerminationMessage

class Lifecycle:

    # NOTE:
    # Lifecycle logs provide observability and are intentionally minimal.
    # Do not remove unless replacing with equivalent telemetry.


    def __init__(self, message_hub: MessageHub):
        self.message_hub = message_hub or MessageHub()

    def _lifecycle_ready(self, publisher_id: int):
        self.message_hub.publish(
            topic=TopicsEnum.LIFECYCLE,
            message=ServiceReady(),
            message_context=MessageContext(
                from_id=publisher_id,
            ),
        )

    def _lifecycle_terminated(self, publisher_id: int):
        self.message_hub.publish(
            topic=TopicsEnum.LIFECYCLE,
            message=TerminationMessage(),
            message_context=MessageContext(
                from_id=publisher_id,
            ),
        )
