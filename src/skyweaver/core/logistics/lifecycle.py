# core/logistics/lifecycle.py

from enum import Enum, auto
from typing import Dict, Set, Type
from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.core.bus.messages.lifecycle_message import (
    DependenciesSatisfied,
    NotifyJoinMessage,
    ServiceReady,
    TerminationMessage,
)

class Lifecycle:
    """
    Passive lifecycle state machine.

    Responsibilities:
    - announce join (with declared dependencies)
    - track dependency satisfaction
    - announce ready exactly once
    - announce termination
    """

    def __init__(
        self,
        *,
        publisher_id: int,
        message_hub: MessageHub,
        dependencies: Set[Type] = set(),
    ):
        self.publisher_id = publisher_id
        self.message_hub = message_hub

        self._dependencies: Set[Type] = set(dependencies)
        self._satisfied: Dict[Type, bool] = {
            dep: False for dep in self._dependencies
        }

        self._joined_announced = False
        self._ready_announced = False
        self._satisfied_announced = False
        self.newly_satisfied: set[Type] = set()

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    def notify_join(self):
        if self._joined_announced:
            return

        self._joined_announced = True

        self.message_hub.publish(
            topic=TopicsEnum.LIFECYCLE,
            message=NotifyJoinMessage(
                dependencies=list(self._dependencies)
            ),
            message_context=MessageContext(
                from_id=self.publisher_id,
            ),
        )

        self._evaluate_ready()

    def notify_terminated(self):
        self.message_hub.publish(
            topic=TopicsEnum.LIFECYCLE,
            message=TerminationMessage(),
            message_context=MessageContext(
                from_id=self.publisher_id,
            ),
        )

    def _notify_dependencies_satisfied(self, parcel_types: set[Type]):

            self.message_hub.publish(
                topic=TopicsEnum.LIFECYCLE,
                message=DependenciesSatisfied(parcel_types=parcel_types),
                message_context=MessageContext(
                    from_id=self.publisher_id,
            ),
        )
    # ------------------------------------------------------------------
    # Dependency tracking
    # ------------------------------------------------------------------

    def mark_dependencies_satisfied(self, parcel_types: set[Type]):
        self.newly_satisfied: set[Type] = set()

        for parcel_type in parcel_types:
            if parcel_type not in self._satisfied:
                continue

            if self._satisfied[parcel_type]:
                continue  # já satisfeita → ignora

            self._satisfied[parcel_type] = True
            self.newly_satisfied.add(parcel_type)

        #if newly_satisfied:
        #    self._notify_dependencies_satisfied(newly_satisfied)
        #    self._evaluate_ready()

    def verify_and_notify(self):
        
        if self._satisfied_announced:
            return
        
        if all(self._satisfied.values()):

            self._satisfied_announced = True
            if self.newly_satisfied:

                self._notify_dependencies_satisfied(self.newly_satisfied)
                self.newly_satisfied = set()

            #self._notify_dependencies_satisfied(set(self._satisfied.keys()))
            self._evaluate_ready()



    def _evaluate_ready(self):
        if self._ready_announced:
            return

        if all(self._satisfied.values()):
            self._ready_announced = True
            self._notify_ready()

    def _notify_ready(self):
        self.message_hub.publish(
            topic=TopicsEnum.LIFECYCLE,
            message=ServiceReady(),
            message_context=MessageContext(
                from_id=self.publisher_id,
            ),
        )


