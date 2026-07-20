from dataclasses import dataclass, field
from uuid import UUID, uuid4
from abc import ABC


@dataclass(frozen=True, slots=True)
class Identity(ABC):

    name: str
    uuid: UUID = field(
        init=False,
        default_factory=uuid4,
    )

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class FlowId(Identity):
    pass


@dataclass(frozen=True)
class BusId(Identity):
    pass


@dataclass(frozen=True)
class NodeId(Identity):
    flow: FlowId


@dataclass(frozen=True)
class DepotId(Identity):
    bus: BusId


@dataclass(frozen=True)
class LogisticsId(Identity):
    depot: DepotId

    @property
    def bus(self) -> BusId:
        return self.depot.bus


@dataclass(frozen=True)
class OutpostId(Identity):
    logistics: LogisticsId
    node: NodeId

    @property
    def flow(self) -> FlowId:
        return self.node.flow

    @property
    def bus(self) -> BusId:
        return self.logistics.depot.bus

    @property
    def depot(self) -> DepotId:
        return self.logistics.depot

    @property
    def qualified_name(self) -> str:
        return f"{self.logistics.name}/" f"{self.flow.name}/" f"{self.node.name}"
