from dataclasses import dataclass
from typing import Callable

from skyweaver.core.flow.node.node_definition import (
    NodeDefinition,
    NodeKind,
)
from skyweaver.core.flow.node.propagation_policy import PropagationPolicy
from skyweaver.core.identifier.identifier import FlowId, NodeId
from skyweaver.core.logistics.endpoint.outpost_builder import OutpostBuilder
from skyweaver.core.logistics.endpoint.role import Role
from skyweaver.core.logistics.endpoint.status.status import Status
from skyweaver.core.logistics.logistics import Logistics

_UNSET = object()


@dataclass(eq=False)
class Node:
    flow_id: FlowId
    definition: NodeDefinition
    function: Callable
    logistics: Logistics
    status_changes_enabled: bool = True

    def __post_init__(self) -> None:
        """
        Completes Node local runtime wiring using two-phase initialization.

        Phase 1 creates the Node identity and its Outpost instance, but does not
        allow the Outpost to start external synchronization yet.

        This separation is required because the Node must first attach its
        `_on_status_changed` callback to the Outpost. Only after that callback is
        installed may the Outpost begin registration and initial Depot sync.

        Without this two-phase initialization, the Outpost could receive its
        initial pallet before the Node is fully wired, causing dependency changes
        to be detected without triggering `process()`.
        """

        self.identity = NodeId(
            self.definition.name,
            flow=self.flow_id,
        )

        self._output_result = _UNSET

        self._outpost = OutpostBuilder(
            description=self.definition.description,
        ).build(
            node_id=self.identity,
            logistics=self.logistics,
        )

        self._outpost.set_on_status_changed(
            self._on_status_changed,
        )

        self._produced = tuple(
            self._outpost.schema().descriptors_by_role(Role.PRODUCED).keys()
        )

        try:
            self._outpost.start()
        except Exception:
            self.close()
            raise

    # ======================================================
    # Invalidation Propagation Mechanism
    # ======================================================

    def _should_run(
        self,
        status: Status,
    ) -> bool:

        match self.definition.propagation_policy:

            case PropagationPolicy.ANY_DEPENDENCY_CHANGED:
                return any(status.any_dependencies_dirty(p) for p in self._produced)

            case PropagationPolicy.ALL_DEPENDENCIES_CHANGED:
                return all(
                    self._all_required_dependencies_dirty(status, produced)
                    for produced in self._produced
                )

            case PropagationPolicy.MANUAL:
                return False

        raise RuntimeError(
            f"Unsupported propagation policy: {self.definition.propagation_policy!r}"
        )

    def _all_required_dependencies_dirty(
        self,
        status: Status,
        produced: type,
    ) -> bool:
        descriptor = self._outpost.schema().descriptor(produced)
        dependency_flags = status.dependency_flags.get(produced, {})
        required_dependencies = descriptor.depends_on - descriptor.optional_depends_on

        if not any(flag.name == "DIRTY" for flag in dependency_flags.values()):
            return False

        return all(
            dependency_flags.get(dependency) is not None
            and dependency_flags[dependency].name == "DIRTY"
            for dependency in required_dependencies
        )

    def _on_status_changed(
        self,
        status: Status,
    ) -> None:
        if not self.status_changes_enabled:
            return

        if not self._should_run(status):
            return

        self.process()

    # ======================================================
    # Public API
    # ======================================================

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def kind(self) -> NodeKind:
        return self.definition.kind

    @property
    def output_result(self):

        if self._output_result is _UNSET:
            return None

        return self._output_result

    @property
    def output_was_produced(self) -> bool:
        return self._output_result is not _UNSET

    def reset_output(self) -> None:
        self._output_result = _UNSET

    def enable_status_changes(self) -> None:
        self.status_changes_enabled = True

    def close(self) -> None:
        if hasattr(self, "_outpost"):
            self.logistics.depot.sentinel.unregister(type(self._outpost))
            self._outpost.close()

    # ======================================================
    # Runtime
    # ======================================================

    def process(self) -> None:

        arguments = self._build_function_arguments()

        result = self.function(
            *arguments,
        )

        if self.kind == NodeKind.OUTPUT:
            self._output_result = result
            self._outpost._status_manager.clear()
            return

        self._write_function_result(result)

    def invoke_input(
        self,
        *args,
        **kwargs,
    ) -> None:

        if self.kind != NodeKind.INPUT:
            raise RuntimeError(f"Node '{self.name}' is not an input node.")

        result = self.function(
            *args,
            **kwargs,
        )

        self._write_function_result(result)

    # ======================================================
    # Helpers
    # ======================================================

    def _build_function_arguments(
        self,
    ) -> list[object]:

        arguments: list[object] = []

        for (
            parameter_name,
            parcel_type,
        ) in self.definition.description.consumed_parameters:
            descriptor = self._outpost.schema().descriptor(parcel_type)
            arguments.append(getattr(self._outpost, descriptor.field_name))

        return arguments

    def _write_function_result(
        self,
        result,
    ) -> None:

        descriptors = list(
            self._outpost.schema().descriptors_by_role(Role.PRODUCED).values()
        )

        if len(descriptors) == 0:
            return

        if len(descriptors) == 1:

            with self._outpost:
                setattr(
                    self._outpost,
                    descriptors[0].field_name,
                    result,
                )

            return

        if not isinstance(result, tuple):
            raise RuntimeError(
                f"Node '{self.name}' must return {len(descriptors)} values."
            )

        if len(result) != len(descriptors):
            raise RuntimeError(
                f"Node '{self.name}' returned "
                f"{len(result)} values but "
                f"{len(descriptors)} were expected."
            )

        with self._outpost:

            for descriptor, parcel in zip(
                descriptors,
                result,
                strict=True,
            ):
                setattr(
                    self._outpost,
                    descriptor.field_name,
                    parcel,
                )
