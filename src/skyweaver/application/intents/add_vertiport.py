from dataclasses import dataclass


@dataclass(frozen=True)
class AddVertiport:
    """
    Application-level intent representing the insertion of a vertiport
    from external GIS/web interfaces.

    Responsibilities:
    - transport frontend spatial interaction into the application layer;
    - expose a web-friendly geographic boundary for interactive tools;
    - decouple frontend GIS coordinates from internal hexagonal structures;
    - preserve the separation between geographic space and operational
      discretization.

    Frontend expectations:
    - the frontend operates entirely in WGS84 geographic coordinates;
    - MapLibre/deck.gl interactions emit longitude/latitude values;
    - frontend consumers must never manipulate HexCoord directly.

    Architectural rationale:
    - HexCoord belongs to the internal operational domain model;
    - the frontend should communicate using geographic coordinates only;
    - geographic-to-local and local-to-hex transformations must occur
      inside the application/runtime pipeline;
    - this intent acts as the spatial boundary crossing between:

          Web GIS Space (WGS84)
                  ↓
          Application Intent Layer
                  ↓
          Domain Projection Pipeline
                  ↓
          Local Continuous Space
                  ↓
          Hexagonal Operational Space

    This separation prevents frontend coupling to:
    - hexagonal discretization;
    - routing internals;
    - operational spatial indexing.
    """

    latitude: float
    longitude: float
