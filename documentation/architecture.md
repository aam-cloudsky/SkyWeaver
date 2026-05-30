```md
# SkyWeaver Architecture Overview

## Purpose of This Document

This document is the first architectural description of the `SkyWeaver` codebase. Its goal is to help future readers, especially the project author, quickly recover:

- what the system is trying to do
- how it was structured
- why certain abstractions were introduced
- what is already solid
- what is still exploratory or transitional

This is not a low-level API reference. It is a conceptual and structural guide.

---

## Project Intent

`SkyWeaver` is being built as a modular system for spatial planning and routing over an urban airspace representation.

At a high level, the system:

1. loads geospatial input data
2. defines an operational domain
3. projects that data into a local metric frame
4. discretizes the domain into a hexagonal grid
5. applies restrictions to cells
6. computes route structures over the grid
7. derives metrics from those routes
8. visualizes the resulting state

The key architectural intention is that these stages should not be tightly coupled through direct object references or procedural scripts. Instead, they should communicate through explicit data contracts.

---

## Core Architectural Idea

The central idea of the system is:

> each module declares what data it consumes and what data it produces, and all shared state is synchronized through a central authority.

That authority is the `Depot`.

The interface of each module with the shared state is an `Outpost`.

The data itself is represented as `Parcel`s.

The executor of a transformation is an `OperationalUnit`.

This gives the codebase a strong dataflow-oriented architecture.

---

## Main Concepts

## `Parcel`

A `Parcel` is the semantic unit of shared data in the system.

Examples include:

- geodata
- domain
- grid
- heliports
- vertiports
- routes
- graphs

A parcel is not just a Python object. It is intended to be part of the system-wide synchronized state.

File:
- [parcel.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/parcel.py)

### Design intention

The purpose of `Parcel` is to make shared state explicit and typed. Instead of modules passing arbitrary values to one another, they publish and consume named domain objects.

---

## `Outpost`

An `Outpost` is the declarative IO boundary of a module.

An outpost is a dataclass whose fields are parcels, and each parcel is annotated with a role:

- `CONSUMED`
- `PRODUCED`
- `MUTATES`

This makes every module’s contract visible in code.

File:
- [outpost.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/outpost.py)

### Design intention

The `Outpost` abstraction exists to answer:

- what does this module need?
- what does this module publish?
- what state is it allowed to mutate?

This is one of the strongest ideas in the architecture. It gives the codebase a schema-level description of inter-module dependencies.

### Important behavior

`Outpost` enforces mutation discipline.

Direct assignment is blocked unless it happens inside:

```python
with outpost:
    ...
```

This means that parcel mutations are treated as transactions.

That is a major architectural choice: the system is trying to make shared-state mutation explicit and controlled.

---

## `Depot`

The `Depot` is the central store of shared truth.

It stores the latest registered parcels and answers `GET` / `SET` requests from outposts. It is also responsible for broadcasting updates to listeners.

File:
- [depot.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/depot.py)

### Design intention

The project assumes that there is a single authoritative state for the environment. That is why the `Depot` exists.

This fits the domain well. Airspace, routes, restrictions, terminals, and derived graphs are not supposed to drift into separate conflicting copies.

### Architectural role

The depot is:

- the shared memory of the system
- the synchronization hub
- the publication target for produced parcels

---

## `Sentinel`

The `Sentinel` tracks validity and invalidation across derived parcels.

File:
- [sentinel.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/logistics/validity/sentinel.py)

### Design intention

The idea behind the `Sentinel` is very important:

> derived data should become invalid automatically when its dependencies change.

For example:

- if a source parcel changes
- then a derived parcel depending on it may no longer be valid

This is a strong conceptual move. It shows that the project is not only storing state, but also trying to track the correctness status of derived artifacts.

### Current status

The validity system exists and is meaningful, but it is not yet fully exploited by the higher-level orchestration. The conceptual direction is solid.

---

## `OperationalUnit`

An `OperationalUnit` is the execution component of a module.

It owns an outpost and exposes a `run()` method.

File:
- [operational_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/core/operations/operational_unit.py)

### Design intention

The `OperationalUnit` abstraction is intentionally small. It is not a complex framework object. It is simply the operational logic associated with one declarative outpost.

This simplicity is good. It keeps the architecture understandable.

---

## Architectural Layers

The codebase is currently organized into three broad layers.

## 1. `core`

The `core` layer provides infrastructure:

- messaging
- synchronization
- logistics
- lifecycle
- validity
- base operational abstractions

This layer is not domain-specific. It is the execution model.

## 2. `units`

The `units` layer contains domain capabilities.

Each unit performs a transformation over the shared state. This is where the actual airspace/planning logic lives.

Examples:

- YAML loading
- sources loading
- domain construction
- geodata alignment
- grid generation
- restriction application
- routing
- visualization

## 3. `application`

The `application` layer orchestrates units for a concrete use case.

This is where user interaction, sequencing, and higher-level policy should live.

At the moment, this layer exists, but it is still evolving.

---

## Pipeline of the Current System

The current pipeline can be understood as:

```text
YAML -> Sources -> Domain -> Alignment -> HexGrid -> Restriction -> Routes -> Visualization
```

Each stage publishes data that downstream stages consume.

---

## Units and Their Roles

## `YAMLLoaderUnit`

File:
- [yaml_loader_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/yaml_loader/yaml_loader_unit.py)

### Responsibility

Loads configuration from YAML and publishes it as a parcel.

### Intent

Configuration should also be treated as shared state, not as hidden constructor parameters spread across the codebase.

---

## `SourcesUnit`

File:
- [sources_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/sources/sources_unit.py)

### Responsibility

Obtains geospatial input data.

It supports two modes:

- real loading from file
- simulated loading

### Intent

The system is being designed to support both real-world ingestion and experimentation. That is why the source layer already includes simulation behavior.

This is useful during the exploratory phase.

---

## `DomainUnit`

File:
- [domain_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/domain/domain_unit.py)

### Responsibility

Builds the domain from spatial layers.

It uses:

- geodata inputs
- YAML parameters
- projection policy
- `DomainBuilder`

### Intent

The domain is not just a bounding box. It is a local operational frame with a chosen CRS, a center, and bounds.

This is one of the most conceptually important parts of the system: it converts raw geospatial data into a local, operationally meaningful coordinate system.

---

## `AlignmentUnit`

File:
- [alignment_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/geodata_domain_alignment/alignment_unit.py)

### Responsibility

Projects source geodata into the local domain frame.

### Intent

This unit separates:

- loading raw geodata
- adapting that data to the local computational frame

That separation is correct. It avoids mixing GIS ingestion concerns with local planning concerns.

---

## `HexGridUnit`

File:
- [hexgrid_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/hexgrid/hexgrid_unit.py)

### Responsibility

Builds a hexagonal grid over the domain.

### Intent

The continuous operational space is discretized into cells so that routing and constraints can be expressed combinatorially.

The grid is not just a rendering tool. It is the planning substrate.

---

## `RestrictionUnit`

File:
- [restriction_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/restriction/restriction_unit.py)

### Responsibility

Applies hard restrictions to grid cells.

Currently it works incrementally by comparing current heliport cells with previously restricted heliport cells.

### Intent

Restrictions are modeled as changes to cell state, not as a separate overlay graph.

That is a strong modeling choice: the grid itself carries navigability status.

### Current tradeoff

This unit keeps local incremental state:

```python
self._prev_heliport_cells
```

That is practical, but it introduces a local cache alongside the shared architecture. It is not wrong, but it is one of the places where the codebase is balancing architectural purity with operational convenience.

---

## `RoutesUnit`

File:
- [routes_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/routes_unit.py)

### Responsibility

Builds routing artifacts from the current grid and current vertiports.

It computes:

- `AirspaceGraphPack`
- `RoutesGraphPack`
- `TerminalsGraphPack`

### Intent

This unit is trying to centralize route-related state and route-related graph transformations.

It is also trying to protect route semantics, for example by preventing vertiports from being placed on unavailable or heliport cells.

### Important note

This unit is both:

- a route generator
- a route-facing manipulation point for vertiports

That is practical, but it also shows that the application layer is not yet fully stabilized. Some policy logic still leaks into the unit.

---

## `VisualizationUnit`

File:
- [viz_unit.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/visualization/viz_unit.py)

### Responsibility

Displays the current system state.

It renders:

- grid
- heliports
- vertiports
- routes
- metrics

It also captures mouse clicks and forwards them through callbacks.

### Intent

The unit is designed to be a view, not the owner of domain logic. It should render state and emit interaction events upward.

That separation is conceptually correct, even if some interaction policy is still being worked out at the application layer.

---

## Spatial Modeling

## `Domain`

File:
- [domain.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/domain/frame/domain.py)

The `Domain` encapsulates:

- projected center
- operational bounds
- visualization bounds
- local frame transformation

### Intent

The domain is more than “where the grid goes”. It is the geometric reference frame in which planning becomes computationally meaningful.

---

## `Bounds`

File:
- [bounds.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/domain/frame/bounds.py)

`Bounds` represents rectangular spatial limits and provides:

- range-based construction
- corners
- polygon
- containment
- expansion

### Intent

This object exists to give explicit structure to rectangular operating areas instead of treating them as loose tuples.

---

## `HexGrid` and `HexCell`

Files:
- [hexgrid.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/hexgrid/structure/hexgrid.py)
- [hexcell.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/hexgrid/structure/hexcell.py)

The `HexGrid` is the spatial container.
The `HexCell` is the operational atomic element.

Each cell has:

- coordinate
- size
- state
- cost

### Intent

The grid abstracts away geometry/topology details so that higher-level planning can work over cells as domain entities.

---

## Routing Architecture

## `GraphPack`

File:
- [graph_pack.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/graph/graph_pack.py)

`GraphPack` wraps an `igraph.Graph` and maintains explicit maps:

- `cell -> vertex id`
- `vertex id -> cell`

There are three concrete graph pack types:

- `AirspaceGraphPack`
- `RoutesGraphPack`
- `TerminalsGraphPack`

### Intent

The purpose of `GraphPack` is to prevent route logic from depending on implicit `igraph` internals.

This is a good abstraction. It gives semantic meaning to the graph and exposes the mapping that the domain actually needs.

---

## Graph Levels

The route subsystem uses three graph levels.

### `G0`: `AirspaceGraphPack`

Base graph of traversable cells and their adjacency.

### `G1`: `RoutesGraphPack`

Graph induced by the union of paths between terminals.

This graph also stores:

```python
paths: List[List[HexCell]]
```

That means each element of `paths` is a shortest path between one pair of terminals.

### `G2`: `TerminalsGraphPack`

Terminal-to-terminal connectivity graph, where each edge represents a route between terminals.

### Intent

This layered decomposition separates:

- navigable substrate
- realized route structure
- terminal connectivity abstraction

That is a strong and domain-meaningful design.

---

## `GraphBuilder`

File:
- [graph_builder.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/graph/graph_builder.py)

### Responsibility

Builds `G0`, `G1`, and `G2`.

### Current architectural direction

The file currently states:

> topology only, weight computation should not live here

That is a very important statement. It means the system is moving toward this distinction:

- `G0` should capture connectivity
- routing cost should be evaluated dynamically

This is a healthy direction, because it reduces stale-weight problems and clarifies responsibilities.

---

## `Routing`

File:
- [routing.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/routes/routing.py)

### Responsibility

Computes shortest paths over `G0`.

It currently uses:

- a unit step cost
- plus average cell cost across each traversed edge

### Intent

The route cost model is trying to represent two things:

- motion itself has a cost
- traversing costly cells adds penalty

This avoids the pathological case where many zero-cost cells make long and short routes appear equivalent.

### Important conceptual point

`Routing` has been moving away from internal stored graph state and toward stateless computation over a passed `AirspaceGraphPack`.

That is a good architectural correction. It reduces hidden stale-state bugs.

---

## Metrics

File:
- [metrics.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/units/analysis/metrics.py)

Current metrics include:

- average path length
- path-based cell betweenness

### Intent

Metrics are computed over route realizations, not raw topology. This makes them operationally meaningful.

The current implementation is still intentionally simple and exploratory. It is not yet a fully generalized metrics framework.

---

## Current Application Layer

Files:
- [routes_app.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/routes_app.py)
- [intent.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/intent.py)
- [dispatcher.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/dispatcher.py)
- [hex_app_controller.py](/Users/Davi/Documents/GitHub/SkyWeaver/src/skyweaver/application/hex_app_controller.py)

### Current reality

There are two application-layer directions visible in the code.

#### 1. Pragmatic orchestrator

`RoutesApp` is the active orchestration entry point.

It:

- instantiates the main units
- executes them in order
- applies UI interaction policies

#### 2. Intent-driven experiment

There is also a partially formed command/intent architecture using:

- `HexIntent`
- `IntentDispatcher`
- `HexApplicationController`

This seems to be an experiment toward a cleaner event-driven application layer.

### Interpretation

This tells us the codebase is in a transition phase:

- the need for an application layer has already been recognized
- the final shape of that layer has not yet been fully consolidated

This is normal in an exploratory project.

---

## Code Style and Structural Patterns

The codebase currently uses the following patterns consistently.

## 1. Dataclass-based schemas

Outposts and many parcels are declarative dataclasses.

### Why this matters

It keeps data contracts explicit and easy to inspect.

## 2. Transactional mutation

Outpost mutation happens inside:

```python
with outpost:
    ...
```

### Why this matters

It prevents silent arbitrary state mutation and makes publication intent visible.

## 3. Domain-first naming

Names like:

- `Domain`
- `Bounds`
- `HexGrid`
- `HexCell`
- `AirspaceGraphPack`
- `RoutesGraphPack`
- `TerminalsGraphPack`

show a clear attempt to make the code reflect the modeled world rather than low-level implementation artifacts.

## 4. Separation of geometry, topology, routing, and visualization

These concerns are not collapsed into one module. That is good.

## 5. Explicit TODO-driven evolution

The code contains many TODOs. This is not just unfinished work; it documents active architectural questions.

That is useful during exploration, but eventually these TODOs should migrate into either:
- documented design decisions
- issues
- or concrete refactors

---

## Strengths of the Current Architecture

The strongest aspects of the current codebase are:

- It has a real architecture, not just a growing script.
- The `Depot` / `Outpost` / `Parcel` system gives the project a strong conceptual backbone.
- Dependencies are declared explicitly.
- Spatial transformation stages are well separated.
- Graph semantics are being given explicit wrappers.
- The system is already thinking in terms of derived-state validity, which is a mature concern.

---

## Current Weaknesses and Transitional Areas

The main transitional or risky areas are:

- The application layer is not fully stabilized.
- Some domain rules are still split between app code, units, and UI callbacks.
- Some units still carry local cached state that competes with the shared-state philosophy.
- There are remnants of earlier naming and refactor stages.
- The validity system exists, but orchestration does not yet fully rely on it.

These are not signs of failure. They are signs of a codebase that already has a strong architectural idea and is still converging on its cleanest practical form.

---

## Architectural Summary in One Paragraph

SkyWeaver is a modular spatial planning system built around shared typed state. Each module declares its inputs and outputs through outposts, publishes semantic parcels to a central depot, and participates in a pipeline that transforms raw geodata into domain-aligned coordinates, discretized hex cells, restricted operational space, route graphs, and visualization artifacts. The architecture strongly favors explicit contracts, modular derived-state computation, and separation between infrastructure, domain units, and orchestration logic.

---

## What Future You Should Remember

If you return to this code in a few months, the most important thing to remember is:

- the project was not designed as a direct procedural pipeline only
- it was designed as a modular system with explicit state contracts
- `Depot` is the shared truth
- `Outpost` is the boundary of each module
- `OperationalUnit` is the executor
- the pipeline is spatial and staged
- the application layer is where user-policy logic is supposed to consolidate

The architecture is already meaningful. The next phase is not inventing a new one, but consolidating the current one.

---

## Suggested Next Documentation Files

After this file, the next useful documents would be:

- `CORE_CONCEPTS.md`
- `ROUTING_MODEL.md`
- `APPLICATION_LAYER.md`
- `VALIDITY_SYSTEM.md`

This file should remain the highest-level architectural entry point.
```