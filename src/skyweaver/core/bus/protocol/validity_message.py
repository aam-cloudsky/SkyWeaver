from dataclasses import dataclass
from skyweaver.core.bus.protocol.base_message import BaseMessage
from skyweaver.core.bus.runtime.publisher_manager import PublisherID
from skyweaver.core.logistics.validity.validity_transition import ValidityTransition


@dataclass(frozen=True)
class ValidityMessage(BaseMessage):
    validity_transition: ValidityTransition
    validity_source_id: PublisherID
