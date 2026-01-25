
from dataclasses import dataclass, field
from skyweaver.core.logistics.parcel import Parcel
import igraph 

@dataclass
class GraphParcel(Parcel):
    navigation_graph: igraph.Graph = field(default_factory=igraph.Graph)
    shortest_path_graph: igraph.Graph = field(default_factory=igraph.Graph)
    terminal_graph: igraph.Graph = field(default_factory=igraph.Graph)


    def is_resolved(self) -> bool:
        print("[GraphParcel] PRECISO RESOLVER ISSO.")
        return (self.navigation_graph is not None and
                self.shortest_path_graph is not None and
                self.terminal_graph is not None)