```markdown
# SkyWeaver

SkyWeaver is a GIS-oriented operational sandbox for modeling urban airspace, infrastructure, routing, and future autonomous aerial operations.

It is not a simple map viewer and not only a routing experiment. The project is evolving toward a modular spatial runtime where:

- the **core** owns operational state and routing logic;
- the **application layer** translates runtime state into GIS-safe scene data;
- the **server** transports that scene to external clients;
- the **frontend** renders and interacts with the system in WGS84 geographic space.

---

# Current Intent

SkyWeaver is being built to support:

- urban airspace organization;
- operational routing experiments;
- droneport / vertiport planning;
- restriction modeling;
- future spatial optimization and simulation;
- reactive GIS visualization.

The current system already has a strong architectural direction:

- synchronous core execution;
- strongly typed parcels and outposts;
- explicit runtime orchestration;
- GIS materialization boundaries;
- frontend/backend separation.

---

# Core Philosophy

SkyWeaver intentionally favors:

- **explicit orchestration**
- **strong runtime boundaries**
- **typed operational state**
- **clear GIS conversion layers**
- **frontend isolation from engine internals**

The project does **not** want the frontend to know:

- `Parcel`
- `Outpost`
- `HexCoord`
- `HexCell`
- `HexGrid`
- local cartesian coordinates
- internal CRS details

Instead, the frontend should only consume **transport-safe GIS scenes**.

---

# High-Level Architecture

```text
Core / Operational Runtime
    ↓
Application Runtime Synchronization
    ↓
GIS Materialization
    ↓
Transport Serialization
    ↓
WebSocket / HTTP
    ↓
Frontend Runtime Store
    ↓
MapLibre / deck.gl Visualization
```

More concretely:

```text
Depot
    ↓
RuntimeOutpost
    ↓
ApplicationRuntime
    ↓
SceneMaterializer
    ↓
SceneSnapshot
    ↓
TransportScene
    ↓
FastAPI + WebSocket
    ↓
Pinia runtimeStore.scene
    ↓
Vue + MapLibre + deck.gl
```

---

# The Core

## What the core is

The core is the operational engine of SkyWeaver.

It is responsible for:

- loading and synchronizing state;
- projecting spatial data into a local operational frame;
- discretizing the domain into hexagonal space;
- applying restrictions;
- building routing graphs;
- recomputing route structures after mutations.

The core is intentionally:

- **synchronous**
- **strongly typed**
- **explicitly orchestrated**
- **reactive through state synchronization**
- **independent from frontend concerns**

## Why synchronous?

The core does not rely on hidden asynchronous cascades.

Instead, it prefers explicit runtime steps like:

```python
units.routes.run()
```

This improves:

- traceability;
- reproducibility;
- debugging clarity;
- scientific/operational transparency.

That choice is especially important in a project that may later become:

- a planning tool;
- an operational GIS;
- a simulation platform;
- a research artifact.

---

# Depot / Outpost / Parcel

This is one of the most important concepts in SkyWeaver.

## Parcel

A `Parcel` is the semantic unit of shared state.

Examples:

- `DomainParcel`
- `GridParcel`
- `HeliportsParcel`
- `VertiportsParcel`
- `RoutesParcel`
- `YAMLParcel`

A parcel is **not** a frontend DTO.  
It is an internal runtime state object.

## Outpost

An `Outpost` is the synchronization boundary of a unit.

It declares which parcels are:

- `CONSUMED`
- `PRODUCED`
- `MUTATES`

This is extremely important because it makes runtime dependencies explicit.

## Depot

The `Depot` is the synchronized shared state hub.

It acts as the operational state registry and propagation center.

In practice:

- units publish parcels into the `Depot`;
- other outposts receive synchronized updates;
- runtime consumers can observe coherent snapshots.

## Why this matters

This model gives SkyWeaver:

- explicit state ownership;
- reactive propagation without ad hoc shared globals;
- clearer architectural contracts;
- a strong basis for future simulation and scenario work.

---

# Runtime Synchronization

SkyWeaver uses a runtime synchronization pattern built around:

- `Depot`
- `Outpost`
- `RuntimeOutpost`
- `ApplicationRuntime`

## RuntimeOutpost

`RuntimeOutpost` is the runtime-facing outpost used by the application layer.

It consumes the parcels required to build the frontend scene:

- `DomainParcel`
- `GridParcel`
- `RoutesParcel`
- `HeliportsParcel`
- `VertiportsParcel`
- `YAMLParcel`

Its job is **not** to render.  
Its job is to receive synchronized runtime state.

## ApplicationRuntime

`ApplicationRuntime` is the live operational boundary of the application layer.

Responsibilities:

- instantiate and bootstrap runtime units;
- observe synchronized parcel pallets from `RuntimeOutpost`;
- trigger scene materialization;
- hold the current scene snapshot;
- notify scene subscribers.

This is the object that turns core runtime state into something externally consumable.

---

# Application Layer

The application layer is the bridge between:

- the operational core
- external interfaces such as:
  - frontend
  - HTTP
  - WebSocket
  - future CLI / automation / simulation control

It is responsible for:

- runtime bootstrap;
- command dispatch;
- scene exposure;
- runtime access boundaries.

## Main elements

### `RuntimeUnits`
Container for the core units used in runtime bootstrap.

### `ApplicationRuntime`
Coordinates runtime synchronization and scene recomputation.

### `ApplicationContext`
Acts as the façade exposed to external adapters.

### `IntentDispatcher`
Maps application intents to handlers.

### Handlers
Perform application-level mutations.

Examples:

- `AddVertiportHandler`
- `RemoveVertiportHandler`
- `ToggleRestrictionHandler`

---

# GIS Boundary

A critical architectural decision in SkyWeaver is this:

> the frontend operates **only in WGS84 geographic coordinates**

That means:

- frontend tools emit `longitude`, `latitude`
- frontend never manipulates `HexCoord`
- frontend never sees local cartesian space
- frontend never sees hex discretization directly

The conversion pipeline is:

```text
Frontend (WGS84)
        ↓
Application Intent Layer
        ↓
Domain Projection
        ↓
Local Continuous Cartesian Space
        ↓
Hexagonal Operational Space
```

This boundary is essential.

It prevents the frontend from coupling to:

- hex discretization internals;
- routing graph internals;
- local operational coordinate systems;
- domain CRS implementation details.

---

# Continuous Local Space

The runtime does not route directly in geographic coordinates.

Instead, it uses a **local continuous cartesian space**.

Why?

Because operational geometry becomes easier and more stable when expressed in a local projected frame.

This local frame is used before discretization to support:

- metric reasoning;
- domain-relative geometry;
- hex projection;
- spatial indexing.

So the flow is:

```text
Geographic CRS
    ↓
Domain CRS
    ↓
Local Continuous Space
    ↓
Hexagonal Operational Space
```

This is a very important concept in the project.

---

# Hexagonal Operational Space

SkyWeaver discretizes the local continuous domain into hexagonal cells.

Why hexagons?

Because hexagonal discretization is useful for:

- neighborhood reasoning;
- route planning;
- directional symmetry;
- operational spatial simplification.

The hex grid is an internal operational structure.

It is useful for:

- routing
- traversability
- restrictions
- graph building
- future simulation and optimization

But it is **not** the transport boundary for the frontend.

---

# SceneSnapshot vs TransportScene

This is another critical architectural distinction.

## SceneSnapshot

`SceneSnapshot` is an application/runtime object.

It is:

- GIS-aware
- rich
- GeoDataFrame-based
- suitable for spatial materialization and internal GIS reasoning

It contains `MapLayer` objects such as:

- `vertiports`
- `heliports`
- `routes`

## TransportScene

`TransportScene` is the frontend/websocket-safe version of the scene.

It is:

- transport-oriented
- JSON-safe
- GeoJSON-compatible
- WGS84-based

Each transport layer contains:

- `id`
- `geometry_type`
- `crs`
- `geojson`

## Why not send GeoDataFrame directly?

Because `GeoDataFrame` is a GIS object, not a web transport contract.

The frontend needs:

- serialized GeoJSON
- `EPSG:4326`
- stable transport DTOs

So the boundary is intentionally:

```text
SceneSnapshot (GIS-rich)
    ↓
TransportScene (transport-safe)
```

---

# Scene Materialization

`SceneMaterializer` is the GIS projection boundary of the application layer.

Responsibilities:

- consume synchronized runtime parcels;
- build GIS-ready layers;
- transform local runtime state into geographic geodata;
- serialize the scene into WGS84 GeoJSON for transport.

Current layer types include:

- `vertiports`
- `heliports`
- `routes`

Future layers are expected to include:

- restrictions
- hexgrid
- reachability
- operational overlays
- metrics layers
- cluster layers

---

# Server Layer

The backend server is implemented with:

- `FastAPI`
- `WebSocket`

It is responsible for:

- exposing health endpoints;
- exposing the current transport scene;
- exposing mutation intents;
- broadcasting updated transport scenes to connected clients.

Current endpoints include:

- `GET /health`
- `GET /scene`
- `WS /ws`
- `POST /intent/add-vertiport`
- `POST /intent/toggle-restriction`

This server is intentionally thin.

It should not own:

- routing logic
- core GIS logic
- discretization logic
- runtime synchronization logic

It should only expose application/runtime boundaries.

---

# Frontend

The frontend currently uses:

- `Vue 3`
- `Pinia`
- `MapLibre GL`
- `deck.gl`

Its current responsibilities are:

- connect to the WebSocket runtime stream;
- keep the latest `TransportScene` in `runtimeStore.scene`;
- extract layers from the scene;
- render spatial overlays;
- send interactive commands to the backend.

## Current model

The frontend consumes:

```text
TransportScene
    ↓
runtimeStore.scene
    ↓
MapCanvas
    ↓
MapLibre / deck.gl layers
```

## Important principle

The frontend no longer consumes raw parcels.

That is a major architectural improvement.

---

# Current Frontend Direction

The frontend is evolving toward:

- fully reactive GIS visualization;
- runtime-driven scene rendering;
- dynamic websocket updates;
- interactive editing tools;
- layered spatial overlays;
- operational UX rather than raw GIS debugging.

It is intentionally moving away from:

- matplotlib-style debug rendering
- parcel-shaped frontend state
- core/frontend leakage

and toward:

- spatial operational UI
- scene-based rendering
- GIS-safe transport boundaries

---

# Current Functionalities

At the moment, the system is designed to support:

- backend startup via `run_server.py`
- frontend startup via `run_frontend.py`
- combined local startup via `run_system.py`
- YAML loading
- geodata loading
- domain creation
- alignment to local operational space
- hexgrid generation
- route graph generation
- scene materialization
- transport serialization
- websocket scene streaming
- frontend scene consumption
- vertiport rendering
- add-vertiport interaction path
- route recomputation after accepted mutations

---

# Current Limitations

This is important: SkyWeaver is already a real platform architecture, but it is still under active construction.

Current limitations include:

- frontend still renders only part of the scene;
- heliports are not yet fully rendered in the web client;
- routes are not yet fully rendered in the web client;
- restrictions are not yet fully visualized as a scene layer;
- route styling is still primitive;
- mutation robustness is still evolving;
- some websocket mutation paths are still being hardened;
- naming across UI and runtime is still transitional;
- frontend tooling is still experimental;
- layer visibility/control systems are still partial;
- ontology is not yet stabilized.

---

# Ontology and Naming

SkyWeaver currently uses a **transitional ontology**.

Current internal core naming includes:

- `heliports`
- `vertiports`

Expected future semantic direction may evolve toward:

- `heliports -> vertiports`
- `vertiports -> droneports`

But this renaming is intentionally **not being forced into the core yet**.

## Why?

Because the ontology is still stabilizing.

The current strategy is:

- preserve core stability;
- avoid renaming everything prematurely;
- allow temporary semantic aliasing in the application/frontend layer.

This is a classic case of **ubiquitous language still being stabilized**.

---

# How to Run

## Python environment

SkyWeaver uses a Python environment with dependencies declared in `pyproject.toml`.

Recommended approach:

1. create and activate your environment
2. install dependencies
3. ensure `skyweaver` is importable from `src`

Typical workflow:

```bash
poetry install
poetry shell
```

Or your preferred equivalent environment setup.

## Frontend dependencies

The frontend lives in:

```text
frontend/
```

Install dependencies with:

```bash
cd frontend
npm install
```

## Run backend only

```bash
python examples/droneport_experiment/run_server.py
```

## Run frontend only

```bash
python examples/droneport_experiment/run_frontend.py
```

## Run full local system

```bash
python examples/droneport_experiment/run_system.py
```

`run_system.py` orchestrates:

- backend startup
- backend healthcheck wait
- frontend startup
- coordinated shutdown

---

# Runtime Flow

The current runtime flow is:

```text
Frontend / WebSocket / HTTP
        ↓
ApplicationContext
        ↓
IntentDispatcher
        ↓
Application Handlers
        ↓
Runtime Units / Outposts
        ↓
Depot
        ↓
RuntimeOutpost Synchronization
        ↓
ApplicationRuntime
        ↓
SceneMaterializer
        ↓
SceneSnapshot
        ↓
TransportScene
        ↓
WebSocket Push
        ↓
Frontend runtimeStore.scene
```

This is the key operational loop of the platform.

---

# Architectural Patterns Present

The current system already uses several strong patterns.

## Observer
Used in:

- `RuntimeOutpost -> ApplicationRuntime`

The runtime listens for synchronized pallet updates and recomputes the scene reactively.

## Facade
Used in:

- `ApplicationContext`

External systems communicate through a narrow façade rather than touching runtime internals directly.

## Projection / Read Model
Used in:

- `SceneSnapshot`

The runtime does not expose core state directly. It exposes a derived GIS read model.

## Transport DTO
Used in:

- `TransportScene`
- `TransportLayer`

The transport contract is separate from the GIS-rich runtime scene.

## Materializer / Presenter
Used in:

- `SceneMaterializer`

This component converts runtime parcels into GIS-aware scene layers.

## Command Dispatcher
Used in:

- `IntentDispatcher`
- application handlers

Mutations are expressed as semantic intents rather than arbitrary direct state changes.

## Runtime Synchronization Boundary
Used in:

- `Depot`
- `Outpost`
- `Parcel`

This is the backbone of synchronized operational state.

---

# Why This Architecture Matters

SkyWeaver is not just “backend + map frontend”.

It is trying to solve a deeper architectural problem:

- keep a strongly typed operational engine;
- keep GIS projection logic coherent;
- keep the frontend decoupled from discretization internals;
- keep runtime synchronization explicit and observable;
- preserve long-term extensibility for simulation, planning, optimization and operational interfaces.

That is why the system uses these layers.

---

# Planned Visualization Roadmap

Planned frontend GIS features include:

- render heliports
- render routes
- render restrictions / no-fly zones
- render hexgrid
- render reachability layers
- render operational metrics overlays
- show/hide layer system
- droneport / vertiport operational radius overlays
- route highlighting
- route styling improvements
- transparency controls
- selection/inspection tooling
- cluster visualization
- operational heatmaps
- richer scene legend and layer tree

---

# Planned Interactive Roadmap

Planned interactive features include:

- add vertiport
- remove vertiport
- toggle restriction
- dynamic route recomputation
- scenario switching
- operational editing
- richer command tools
- future optimization-driven updates
- future live simulation interactions

---

# Future Architectural Goals

Future goals include:

- stronger runtime/server separation
- richer scene projections
- more explicit transport boundaries
- stronger websocket event architecture
- more robust mutation propagation
- simulation orchestration
- optimization and planning loops
- scenario management
- operational overlays and analysis panels
- ontology stabilization
- stronger frontend modularization

---

# Guidance for Future Contributors

When working on SkyWeaver, keep these rules in mind:

1. Do not expose `Parcel` directly to the frontend.
2. Do not let the frontend manipulate `HexCoord` directly.
3. Keep the frontend in `WGS84`.
4. Keep GIS materialization separate from transport serialization.
5. Keep the core synchronous and explicit unless there is a strong reason not to.
6. Prefer scene-based contracts over parcel-shaped transport payloads.
7. Preserve the distinction between:
   - operational runtime state
   - GIS materialization
   - transport serialization
   - frontend rendering

---

# Project State

SkyWeaver is already beyond the stage of a small experimental script.

It is now:

- a modular GIS-oriented runtime architecture;
- a reactive operational sandbox;
- a growing frontend/backend spatial platform.

It is still evolving, but the core design intent is already strong:

- typed runtime
- synchronized state
- explicit orchestration
- GIS-aware materialization
- frontend-safe transport
- spatial operational UI

That is the foundation the project is building on.
```

# Current Operational Status

SkyWeaver can now:

- bootstrap the full backend runtime;
- synchronize parcels through the Depot;
- materialize GIS scene layers;
- serialize scenes into transport-safe GeoJSON;
- stream scenes through WebSocket;
- render live spatial data in the frontend;
- support interactive vertiport insertion through the web UI;
- recompute routing structures after accepted mutations.

The current frontend/backend loop is now operational.

However, visualization and interaction capabilities are still partial and evolving.


# Current Stack

## Backend
- Python
- FastAPI
- GeoPandas
- Shapely
- NetworkX

## Frontend
- Vue 3
- Pinia
- MapLibre GL
- deck.gl
- TypeScript

## GIS / Spatial
- GeoJSON
- WGS84 (transport boundary)
- Local projected CRS
- Hexagonal discretization

## Runtime
- Depot / Outpost synchronization
- Scene materialization
- Reactive runtime propagation

# Reactive Scene Loop

One of the central ideas of SkyWeaver is that the frontend does not query operational state directly.

Instead:

- runtime mutations update synchronized parcels;
- synchronized parcels trigger scene recomputation;
- scene recomputation generates a new SceneSnapshot;
- SceneSnapshot is serialized into TransportScene;
- TransportScene is streamed to connected clients;
- the frontend reacts to scene updates declaratively.

This creates a reactive GIS architecture centered around scene propagation rather than imperative frontend synchronization.


The SceneMaterializer is one of the most important architectural boundaries in the system.

It isolates:
- operational runtime state;
- GIS projection logic;
- transport serialization concerns.

This prevents GIS concerns from leaking into:
- the frontend;
- transport DTOs;
- runtime synchronization logic.


# Robust Materialization Principle

Scene materializers must support valid empty states.

Examples:
- zero routes
- zero vertiports
- zero restrictions
- empty overlays

Reactive GIS systems naturally transition through transient and partially empty states.

Therefore, every materialized layer should always have a valid empty representation.

The frontend should never:
- compute operational routing;
- manipulate HexCoord directly;
- understand Parcel synchronization;
- depend on runtime discretization internals;
- own operational state truth.

The frontend is a scene consumer and interaction surface.



# Current Visualization Gaps

The runtime already computes more information than the frontend currently renders.

Important missing visual layers include:
- heliports
- routes
- restrictions
- operational radii
- hexgrid overlays
- reachability overlays

This means the runtime currently has richer operational state than the frontend visualization exposes.


# Long-Term Vision

SkyWeaver is evolving toward a spatial operational platform capable of supporting:

- planning;
- simulation;
- operational analysis;
- optimization;
- dynamic scenario evaluation;
- future autonomous aerial operations research.

The current GIS runtime architecture is intentionally being designed to support these future capabilities without forcing major architectural rewrites.