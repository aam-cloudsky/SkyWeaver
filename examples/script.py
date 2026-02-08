from skyweaver.core.logistics.depot import Depot
from skyweaver.units.clustering.operations.cluster_unit import ClusterUnit
from skyweaver.units.domain.domain_unit import DomainUnit
from skyweaver.units.routes.routes_unit import RoutesUnit
from skyweaver.units.sources.sources_unit import SourcesUnit
from shapely.geometry import Point

Depot()

# Get data from sources unit (in this case, simulated heliport and vertiport locations)
SourcesUnit().run()

# computes the centroid and domain boundaries from the heliport and vertiport locations
DomainUnit().run()
ClusterUnit().run()

Depot().show_validity()


RoutesUnit().run()
