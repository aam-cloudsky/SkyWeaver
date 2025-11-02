# src/skyweaver/simulation/base_simulation.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
import numpy as np

from skyweaver.airspace.airspace_state import AirspaceState
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

    def set_distribution(self, distribution: BaseDistribution):
        self.distribution = distribution
        print(f"[INFO] Distribution set → {distribution.__class__.__name__}")


    def set_clustering(self, clustering: BaseClustering):
        self.clustering = clustering
        print(f"[INFO] Clustering set → {clustering.__class__.__name__}")


    def set_optimizer(self, optimizer: BaseVoronoiOptimization):
        self.optimizer = optimizer
        print(f"[INFO] Optimizer set → {optimizer.__class__.__name__}")


    # ==========================================================
    # Stage 1: Distribution
    # ==========================================================
    def run_distribution(self):
        """Generate points according to the distribution strategy."""
        print("[INFO] Running distribution algorithm...")
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
        print("[INFO] Running optimization algorithm...")
        self.optimizer.optimize(10)
        return self.optimizer.voronoi_config