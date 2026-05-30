from dataclasses import dataclass


@dataclass(frozen=True)
class RemoveVertiport:
    """
    Application-level intent representing the removal of a vertiport
    from frontend GIS interactions.

    Responsibilities:
    - transport frontend WGS84 coordinates into the application layer;
    - expose a web-friendly geographic interaction boundary;
    - decouple frontend GIS interactions from internal hexagonal structures;
    - preserve the separation between geographic space and operational
      discretization.

    Frontend expectations:
    - frontend tools operate entirely in WGS84 coordinates;
    - MapLibre/deck.gl interactions emit longitude/latitude values;
    - frontend consumers must never manipulate HexCoord directly.

    Spatial boundary:
        Web GIS Space (WGS84)
                ↓
        Application Intent Layer
                ↓
        Domain Projection Pipeline
                ↓
        Local Cartesian Space
                ↓
        Hexagonal Operational Space
    """

    latitude: float
    longitude: float
