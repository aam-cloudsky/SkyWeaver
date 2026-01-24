
from dataclasses import dataclass, field
from skyweaver.core.logistics.parcel import Parcel
import igraph 

@dataclass
class GraphParcel(Parcel):
    navigation_graph: igraph.Graph = field(default_factory=igraph.Graph)
    shortest_path_graph: igraph.Graph = field(default_factory=igraph.Graph)
    terminal_graph: igraph.Graph = field(default_factory=igraph.Graph)
