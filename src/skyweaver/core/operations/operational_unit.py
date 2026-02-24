from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar, get_args, get_origin

from skyweaver.core.logistics.outpost import Outpost


TOutpost = TypeVar("TOutpost", bound=Outpost)


class OperationalUnit(Generic[TOutpost], ABC):
    OUTPOST_CLS: Type[TOutpost]

    def __init__(
        self,
        outpost: TOutpost,
    ):
        if outpost is None:
            # outpost = self.OUTPOST_CLS()
            raise ValueError(f"Outpost must be provided for {self.__class__.__name__}")

        self._outpost: TOutpost = outpost

    @abstractmethod
    def run(self) -> None: ...
