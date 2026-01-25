from dataclasses import dataclass


# core/logistics/parcel.py

from abc import ABC, abstractmethod


class Parcel(ABC):
    """
    Semantic unit transported via Depot.
    """
    pass


@dataclass
class EmptyParcel(Parcel):
    pass
