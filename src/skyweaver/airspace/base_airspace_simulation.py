# src/skyweaver/simulation/base_simulation.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import numpy as np

from skyweaver.airspace.airspace_state import AirspaceState
from skyweaver.core.bus.message_hub import MessageHub
from skyweaver.core.bus.reserved_id_enum import ReservedIDs
from skyweaver.core.bus.topics_enum import TopicsEnum
from skyweaver.distributions.base_distribution import BaseDistribution
from skyweaver.instance_segmentation.clustering.base_clustering import BaseClustering
from skyweaver.tesselation.optimization.base_voronoi_optimization import BaseVoronoiOptimization


class BaseSimulation(ABC):
    """
    Abstract orchestrator that defines how the simulation pipeline runs.

    Responsibilities:
    - Hold and coordinate Distribution, Clustering, and Optimization components.
    - Maintain a shared AirspaceState (blackboard pattern).
    - Define the pipeline sequence (generate → cluster → optimize).
    - Provide extension hooks for custom scenarios.
    """

    def __init__(
        self,
        rng: Optional[np.random.Generator] = None,
        domain: Optional[tuple[tuple[float, float], tuple[float, float]]] = None,
    ):

        self.rng = rng or np.random.default_rng()
        self.domain = domain or ((-1000, 1000), (-1000, 1000))

        # Shared reactive state
        self.state = AirspaceState()

        self._on_change_callbacks = []
        self._subscribe_to_airspace_state_updates()

    def set_distribution(self, distribution: BaseDistribution):
        self.distribution = distribution

    def set_clustering(self, clustering: BaseClustering):
        self.clustering = clustering

    def set_optimizer(self, optimizer: BaseVoronoiOptimization):
        self.optimizer = optimizer


    # ==========================================================
    # Stage 1: Distribution
    # ==========================================================
    def run_distribution(self):
        """Generate points according to the distribution strategy."""
        self.distribution.generate_points()
        return self.distribution.uav_pois, self.distribution.mav_pois

    # ==========================================================
    # Stage 2: Clustering
    # ==========================================================
    def run_clustering(self):
        """Apply clustering to the distributed points."""
        print("[INFO] Running clustering algorithm...")
        config = self.clustering.fit()
        return config

    # ==========================================================
    # Stage 3: Optimization
    # ==========================================================
    def run_optimization(self):
        """Run Voronoi optimization based on cluster geometry."""
        self.optimizer.optimize(10)
        return self.optimizer.voronoi_config
    
    # ==========================================================
    # Stage 4: Callbacks
    # ==========================================================

    def _subscribe_to_airspace_state_updates(self):
        """Subscribe to AirspaceState update messages to trigger callbacks."""

        hub = MessageHub()
        hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
            publisher_id=ReservedIDs.LOGGER.value,
            subscriber=self._on_airspace_state_update,
        )


    def on_change_state(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback to be notified whenever the state changes."""
        self._on_change_callbacks.append(callback)

    def _on_airspace_state_update(self, message: Dict, context):
        """Triggered automatically by AirspaceState updates."""
        # message already contains only the changed fields
        for cb in self._on_change_callbacks:
            cb(message)
