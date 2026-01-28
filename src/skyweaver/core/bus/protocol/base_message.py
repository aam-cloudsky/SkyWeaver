# core/bus/messages/base_message.py
from dataclasses import dataclass


@dataclass(frozen=True)
class BaseMessage:
    pass
