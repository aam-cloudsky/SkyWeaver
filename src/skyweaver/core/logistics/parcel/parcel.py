# core/logistics/parcel.py


from __future__ import annotations
from dataclasses import dataclass
from abc import ABC
from enum import Enum, auto
from dataclasses import field
from typing import Optional

from skyweaver.core.identifier.identifier import FlowId, NodeId
from skyweaver.core.logistics.parcel.provenance import ParcelProvenance, ParcelVersion


@dataclass
class Parcel(ABC):
    """
    Parcel
    ======

    Parcel is the fundamental semantic unit transported through the
    SkyWeaver runtime and stored in the Depot.

    A Parcel represents an actual published or publishable data object.
    It is not used to represent absence.

    Runtime absence is expressed outside the Parcel itself:
    when an Outpost has not yet received or produced a given Parcel,
    the corresponding field may be `None`.

    This means the runtime distinguishes clearly between:

    - no Parcel available yet (`None` in the owning Outpost field)
    - an actual Parcel instance
    - a published Parcel with provenance and version history

    Unlike traditional message-passing systems, each Parcel embeds its own
    provenance information, allowing the runtime to perform incremental
    execution, dependency tracking and workflow traceability.

    Important:
    the current Flow runtime does not use a special "empty Parcel" instance
    or "version 0 Parcel" to model absence. Absence is represented by the
    lack of a Parcel instance.
    """

    _provenance: ParcelProvenance = field(
        default_factory=ParcelProvenance, init=False, repr=False
    )

    @property
    def provenance(self) -> ParcelProvenance:
        return self._provenance

    @property
    def version(self) -> ParcelVersion:
        return self._provenance.version

    @property
    def dependencies(self) -> dict[type, ParcelVersion]:
        return self._provenance.dependencies

    @property
    def node(self) -> NodeId:
        if self._provenance.node is None:
            raise RuntimeError("Parcel has not been published yet.")

        return self._provenance.node

    @property
    def flow(self) -> FlowId:
        return self.node.flow

    def serialize(self) -> dict:
        """
        Converts parcel into a frontend-safe representation.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} " "does not implement serialize()"
        )

    def record_origin(
        self,
        *,
        previous: Optional[Parcel] = None,
        node_id: NodeId,
        dependencies: Optional[dict[type, ParcelVersion]] = None,
    ) -> None:
        """
        Derives this Parcel from a previous revision.

        When a previous Parcel is provided, its provenance is inherited before
        publishing a new revision. The resulting Parcel becomes the logical
        successor of the previous one.
        """

        if previous is not None:
            self._provenance = previous._provenance.copy()

        self._provenance.advance(
            node=node_id,
            dependencies=dependencies,
        )


@dataclass
class EmptyParcel(Parcel):
    pass
