
from time import sleep
import numpy as np
from shapely.geometry import Point
from skyweaver.airspace.airspace_state import AirspaceState
from skyweaver.airspace.airspace_viewer import AirspaceViewer
from skyweaver.distributions.uav_mav_uav_distribution import UAVMAVUAVDistribution
from skyweaver.instance_segmentation.clustering.hdbscan_clustering import HDBSCANClustering
from skyweaver.tesselation.optimization.differential_genetic_optimization import DifferentialGeneticVoronoiOptimization


viewer = AirspaceViewer()
#viewer.show()

# wait for 1 second
sleep(1)



rng = np.random.default_rng(42)


rng = np.random.default_rng(42)
distribution = UAVMAVUAVDistribution(
    rng=rng,
    n_uav=20,
    n_mav=10,
    domain=((-1000, 1000), (-1000, 1000)),
    center_fraction=0.3,
)


clustering = HDBSCANClustering()
clustering.fit()

voronoi_optimization = DifferentialGeneticVoronoiOptimization()
voronoi_optimization.optimize()


