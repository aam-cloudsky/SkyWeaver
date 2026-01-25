from dataclasses import dataclass


# core/logistics/parcel.py

from abc import ABC, abstractmethod


class Parcel(ABC):
    """
    Semantic unit transported via Depot.
    """

    @abstractmethod
    def is_resolved(self) -> bool:
        """
        True if this parcel represents real, meaningful data.
        False if it's only a structural placeholder.
        """
        pass


@dataclass
class EmptyParcel(Parcel):
    def is_resolved(self) -> bool:
        return False
