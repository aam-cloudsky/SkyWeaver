# core/bus/messages/lifecycle.py
from dataclasses import dataclass
from skyweaver.core.bus.messages.base_message import BaseMessage
from skyweaver.core.bus.topics_enum import TopicsEnum
from typing import Optional


@dataclass(frozen=True)
class TerminationMessage(BaseMessage):
    pass