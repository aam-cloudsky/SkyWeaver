from typing import Any, TypeVar

from skyweaver.core.bus.bus import Bus
from skyweaver.core.identifier.identifier import FlowId, LogisticsId, NodeId, OutpostId
from skyweaver.core.logistics.depot import Depot
from skyweaver.core.logistics.endpoint.outpost import Outpost

OutpostT = TypeVar("OutpostT", bound=Outpost)


class Logistics:
    def __init__(self) -> None:
        self._bus = Bus.create()
        self._depot = Depot(bus=self._bus)
        self.identity: LogisticsId = LogisticsId(
            self.__class__.__name__, self._depot.identity
        )

    @property
    def depot(self) -> Depot:
        return self._depot

    def create_outpost(
        self,
        outpost_type: type[OutpostT],
        node_id: NodeId,
    ) -> OutpostT:

        return outpost_type(bus=self._bus, node_id=node_id, logistics_id=self.identity)
