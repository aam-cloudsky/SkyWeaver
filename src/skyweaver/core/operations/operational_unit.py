from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, Optional, Type, TypeVar

from skyweaver.core.logistics.outpost import Outpost

TOutpost = TypeVar("TOutpost", bound=Outpost)


class OperationalUnit(Generic[TOutpost], ABC):
    OUTPOST_CLS: Type[TOutpost]

    def __init__(self, outpost: Optional[TOutpost] = None):
        if outpost is None:
            outpost = self.OUTPOST_CLS()
        self._outpost: TOutpost = outpost

    @abstractmethod
    def run(self) -> None: ...
