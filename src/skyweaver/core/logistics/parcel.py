# core/logistics/parcel.py

from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum, auto


class ParcelRole(Enum):
    """Role of a parcel in an Outpost."""

    CONSUMED = auto()  # dependency
    MUTATES = auto()  # can change, but it is not the owner
    PRODUCED = auto()  # owned / produced here

    UNDEFINED = auto()  # undefined role


class Parcel(ABC):
    """
    Semantic unit transported via Depot.
    """

    pass

    def serialize(self) -> dict:
        """

        Converts parcel into a frontend-safe representation.

        """

        raise NotImplementedError(
            f"{self.__class__.__name__} " "does not implement serialize()"
        )


@dataclass
class EmptyParcel(Parcel):
    pass
