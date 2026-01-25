# core/bus/messages/lifecycle.py
from dataclasses import dataclass
from typing import Type
from skyweaver.core.bus.messages.base_message import BaseMessage


@dataclass(frozen=True)
class TerminationMessage(BaseMessage):
    pass


@dataclass(frozen=True)
class ServiceReady(BaseMessage):
    pass


@dataclass(frozen=True)
class DependenciesUnavailable(BaseMessage):
    parcels_unavailable: list[type]


@dataclass(frozen=True)
class NotifyJoinMessage(BaseMessage):
    dependencies: list[type]


@dataclass(frozen=True)
class DependenciesSatisfied(BaseMessage):
    parcel_types: set[Type]