from skyweaver.airspace.base_airspace_simulation import BaseSimulation
import numpy as np

from skyweaver.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution
from skyweaver.instance_segmentation.clustering.hdbscan_clustering import HDBSCANClustering
from skyweaver.tesselation.optimization.cmaes_voronoi_optimization import CMAESVoronoiOptimization

class AirspaceSimulation(BaseSimulation):
    """Concrete implementation of BaseSimulation for airspace scenarios."""

    def __init__(
        self,
    ):
        
        domain = ((-1000, 1000), (-1000, 1000))
        rng = np.random.default_rng(42)
        super().__init__(rng, domain)

        self.setup_scenario()


    def setup_scenario(self):
        """Setup the simulation scenario with given components."""
        self.set_distribution(UAVMAVUAVDistribution(
            rng=self.rng,
            n_uav=20,
            n_mav=10,
            domain=self.domain,
            center_fraction=0.3,
        ))
        self.set_clustering(HDBSCANClustering())
        self.set_optimizer(CMAESVoronoiOptimization())

if __name__ == "__main__":

    print("[INFO] AirspaceSimulation initialized.")
    
    simulation = AirspaceSimulation()
    print("Clusters", len(simulation.state.clusters))
    simulation.run_distribution()
    print("Clusters", len(simulation.state.clusters))
    simulation.run_clustering()
    print("Clusters", len(simulation.state.clusters))
    simulation.run_optimization()
    print("Clusters", len(simulation.state.clusters))
    


    

    