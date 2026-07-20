from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Optional

from skyweaver.core.identifier.identifier import FlowId, NodeId


@dataclass(frozen=True, order=True)
class ParcelVersion:
    number: int

    @classmethod
    def pending(cls) -> "ParcelVersion":
        return cls(number=0)

    @classmethod
    def initial(cls) -> "ParcelVersion":
        return cls(number=1)

    def next(self) -> "ParcelVersion":
        return type(self)(number=self.number + 1)


@dataclass
class ParcelProvenance:
    """
    Stores provenance information associated with a Parcel.

    The provenance records how a Parcel was produced and which
    Parcel versions were used during its creation. This information allows
    the system to determine whether a Parcel is still consistent with its
    dependencies and provides a complete history of its origin.

    The collected metadata is intended to support dependency tracking,
    version propagation, traceability and, in the future, reproducible
    computational workflows.

    This design is inspired by provenance-aware scientific workflow systems,
    particularly the FAIR Data Pipeline and the W3C PROV provenance model,
    as well as workflow management systems such as Galaxy, Apache Airflow
    and Kepler.

    Reference:
    Mitchell SN et al. FAIR data pipeline: provenance-driven data management
    for traceable scientific workflows.
    Phil. Trans. R. Soc. A (2022).
    DOI: 10.1098/rsta.2021.0300
    """

    # Origin
    node: Optional[NodeId] = None

    # Version
    version: ParcelVersion = field(default_factory=ParcelVersion.pending)

    # Provenance
    dependencies: dict[type, ParcelVersion] = field(default_factory=dict)

    def advance(
        self,
        *,
        node: Optional[NodeId],
        dependencies: Optional[Mapping[type, ParcelVersion]] = None,
    ) -> None:
        """
        Publishes a new provenance revision.
        A new ParcelVersion is generated and optional provenance metadata
        is updated atomically.
        """

        self.version = self.version.next()

        if node is not None:
            self.node = node

        if dependencies is not None:
            self.dependencies = dict(dependencies)

    def copy(self) -> ParcelProvenance:

        return type(self)(
            node=self.node,
            version=self.version,
            dependencies=dict(self.dependencies),
        )
