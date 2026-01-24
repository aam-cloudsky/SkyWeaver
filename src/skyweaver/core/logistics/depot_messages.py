# core/logistics/depot_messages.py

from dataclasses import dataclass
from typing import Dict
from skyweaver.core.logistics.parcel import Parcel
from skyweaver.core.bus.messages.base_message import BaseMessage


@dataclass(frozen=True)
class DepotUpdate(BaseMessage):
    pallet: Dict[type, Parcel]


@dataclass(frozen=True)
class DepotGet(BaseMessage):
    types: list[type[Parcel]]

@dataclass(frozen=True)
class DepotSet(BaseMessage):
    pallet: Dict[type, Parcel]
