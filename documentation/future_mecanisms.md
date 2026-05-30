Future Mechanisms — SkyWeaver

Purpose of This Document

This document exists to preserve the architectural reasoning and conceptual direction of the SkyWeaver project during its exploratory phase.

The goal is NOT to define the final architecture of the system.

Instead, this document aims to:

* preserve important architectural insights;
* document unresolved tensions;
* explain emerging abstractions;
* clarify what already works;
* register what should NOT be implemented yet;
* and allow future continuation of the project even after long periods without contact with the codebase.

This document is intentionally reflective and architectural in nature.

⸻

Current Situation of the Project

SkyWeaver already possesses a strong architectural foundation.

The project is NOT:

* a collection of scripts;
* a prototype without structure;
* or a monolithic procedural system.

Instead, the project already contains:

* modular execution units;
* explicit synchronization contracts;
* shared typed state;
* operational pipelines;
* domain-oriented abstractions;
* spatial discretization;
* routing infrastructure;
* visualization;
* and geospatial ingestion.

The current architecture is centered around:

* Parcel
* Outpost
* Depot
* OperationalUnit

This architecture is strong for:

* execution;
* synchronization;
* pipeline orchestration;
* explicit dependencies;
* modular transformations.

⸻

Existing Architectural Strength

The current system already solves several difficult architectural problems correctly.

Strong Points

1. Explicit synchronization

The Depot acts as:

* shared truth;
* synchronization authority;
* publication target.

2. Explicit IO contracts

Outpost makes dependencies visible:

* consumed parcels;
* produced parcels;
* mutable parcels.

3. Operational modularity

OperationalUnit encapsulates:

* transformations;
* execution logic;
* orchestration stages.

4. Spatial pipeline already exists

The current pipeline is conceptually:

YAML
    -> Sources
    -> Domain
    -> Alignment
    -> HexGrid
    -> Restrictions
    -> Routing
    -> Visualization

This is already a real architecture.

⸻

The Emerging Problem

The project began as:

* a modular transformation pipeline.

However, during development, a deeper spatial modeling problem began to emerge.

The current architecture is very strong at:

* processing;
* synchronization;
* transformation.

But it is still weak at:

* representing operational spatial composition.

This caused several conceptual tensions.

⸻

Current Symptoms

Several symptoms began appearing during development.

1. Units started carrying spatial semantics

Some units are no longer acting only as:

* processors;
* transformers;
* executors.

Instead, they also began representing:

* persistent spatial meaning;
* operational influence;
* overlays;
* restrictions;
* spatial policy.

Examples:

* RestrictionUnit
* RoutesUnit

These units began carrying:

* world semantics;
* not only processing logic.

⸻

2. The Grid became ambiguous

The HexGrid currently behaves partially as:

* operational representation;
* and partially as “the world itself”.

This creates confusion.

Important emerging insight:

The grid should probably not be the world itself.

Instead:

The grid may be only a derived operational materialization of composed spatial influences.

This is one of the most important architectural insights discovered so far.

⸻

3. Spatial influence became scattered

Spatial influence is currently distributed across:

* Units;
* Parcels;
* Grid;
* Application layer.

Examples:

* restrictions;
* operational costs;
* overlays;
* routing constraints;
* infrastructure effects.

There is still no unified abstraction representing:

* spatial influence itself.

⸻

The Central Emerging Question

The main unresolved architectural question became:

Who represents the operational world BEFORE it becomes grid, routing, restrictions, or metrics?

This is the current missing abstraction.

⸻

The Emergence of Layers

The concept of Layer began to emerge naturally during the project.

Initially, Layer appeared to be:

* semantic organization;
* grouping;
* categorization.

However, that interpretation proved insufficient.

A simple semantic grouping does NOT solve the real architectural tension.

⸻

What Layer Is NOT

The project explicitly rejects several weak interpretations of Layer.

A layer should NOT be:

* just a folder;
* just metadata;
* just a semantic tag;
* just a visualization overlay;
* just an enum;
* just a grouping mechanism.

Those approaches do not solve the real problem.

⸻

What Layer MAY Actually Be

The current best hypothesis is:

A Layer is a spatial operational entity that represents a source of influence over the operational scenario.

This is fundamentally different from:

* Units;
* Parcels;
* or visualization overlays.

⸻

Important Distinction

Unit

Represents:

* execution;
* transformation;
* processing.

Answers:

“What does the system do?”

⸻

Parcel

Represents:

* synchronized data;
* transportable state;
* explicit shared artifacts.

Answers:

“What data circulates through the system?”

⸻

Layer

Potentially represents:

* spatial influence;
* operational semantics;
* compositional world state.

Answers:

“What spatial influence exists in the world?”

⸻

Scenario

Potential future abstraction representing:

* coherent world compositions;
* active layer sets;
* alternative operational worlds.

Answers:

“Which world configuration currently exists?”

⸻

The Most Important Emerging Insight

The architecture may eventually evolve toward:

Spatial Layers
    -> Spatial Composition
    -> Operational Surface
    -> Grid Materialization
    -> Routing / Metrics / Visualization

Instead of:

Units
    -> Grid
    -> Routing

This is a MAJOR conceptual shift.

⸻

Spatial Composition

One of the strongest emerging ideas is:

The operational world may be composed from multiple spatial influences.

Examples:

* heliports;
* droneports;
* weather;
* restrictions;
* demand;
* corridors;
* risk;
* population density;
* traffic;
* temporary overlays.

These influences may coexist simultaneously.

⸻

Derived Layers

Another important emerging concept is:

Layers may be primary or derived.

Primary Layers

Directly loaded from world data.

Examples:

* heliports;
* droneports;
* no-fly zones;
* weather observations.

Derived Layers

Produced from transformations over other layers.

Examples:

* heliport restriction layers;
* risk surfaces;
* operational cost layers;
* preferred corridor layers.

⸻

Important Architectural Consequence

This means:

The operational world may exist independently from the grid.

The grid then becomes:

* a computational substrate;
* a materialized operational representation;
* a discretized surface.

NOT:

* the world itself.

⸻

Why This Matters

This distinction is extremely important.

Without it:

* semantics leak into Units;
* restrictions become procedural;
* overlays become ad hoc;
* costs become scattered;
* scenarios become difficult;
* composition becomes implicit.

With it:

* the world gains explicit representation.

⸻

Current Cognitive Situation

At the current stage of development, the project entered a very cognitively heavy region.

Several difficult concepts appeared simultaneously:

* overlays;
* rollback;
* scenarios;
* propagation;
* layers;
* composition;
* dynamic worlds;
* cost maps;
* simulation;
* operational state composition.

This exceeded the reasonable complexity budget for immediate implementation.

⸻

Critical Strategic Insight

One of the most important discoveries was:

Discovering the final architecture too early is dangerous.

The project still lacks:

* stabilized invariants;
* mature domain constraints;
* validated operational pain points.

Therefore:

* premature generalization is risky.

⸻

What Should NOT Be Implemented Yet

The following systems should NOT be implemented yet.

DO NOT implement now:

* full Layer engine;
* scenario engine;
* rollback framework;
* dependency propagation graph;
* automatic derived layer system;
* spatial composition runtime;
* overlay manager;
* dynamic invalidation framework;
* multi-world synchronization.

Reason:

* the ontology is still emerging;
* invariants are not stabilized;
* the architecture is still exploratory.

⸻

Current Recommended Strategy

The current correct strategy is:

1. Stabilize spatial source ingestion

Generalize:

* YAML;
* spatial sources;
* geodata loading.

⸻

2. Remove hardcoded concepts

Examples:

* heliports;
* vertiports.

Replace with:

* generic spatial sources.

⸻

3. Execute the first experiment

The current highest priority is:

* obtaining operational experimental results.

NOT:

* finalizing architecture.

⸻

Minimal Experimental Goal

The current minimal valid experiment is:

Mega shopping droneports
+
Hex grid
+
Restrictions
+
Shortest-path routing
+
Connectivity metrics
+
Visualization

This already constitutes:

* a valid prototype;
* a publishable exploratory experiment;
* a meaningful operational demonstration.

⸻

Why Experiments Matter Architecturally

Experiments are not only scientific outputs.

They also reveal:

* real architectural pain points;
* missing abstractions;
* invalid assumptions;
* natural domain boundaries.

The architecture should evolve from:

* operational pressure;
* not from hypothetical perfection.

⸻

Current Hypothesis About the Future

The current best hypothesis is that SkyWeaver may eventually evolve into:

A compositional spatial operational modeling system.

Where:

* Layers represent operational influences;
* Units transform or materialize those influences;
* Grids become derived operational substrates;
* Routing operates over composed operational surfaces.

However:

THIS IS STILL A HYPOTHESIS.

It is NOT yet the official architecture.

⸻

Important Warning to Future Self

If reading this months later:

DO NOT immediately restart large architectural redesigns.

Instead:

1. Run experiments first.
2. Observe real friction points.
3. Verify if Layers truly simplify composition.
4. Only then evolve the architecture.

The project already possesses:

* a strong execution architecture;
* a strong synchronization architecture;
* and a valid operational pipeline.

The problem is NOT lack of architecture.

The problem is:

* the emergence of compositional spatial semantics.

⸻

Most Important Architectural Insight So Far

Perhaps the strongest insight discovered during this phase was:

The operational grid may not be the world itself, but rather a derived operational materialization of composed spatial influences.

This insight may become one of the foundational ideas of the future SkyWeaver architecture.

⸻

Final Strategic Guidance

Current priority order:

1. Stabilize spatial source ingestion
2. Generalize source loading
3. Execute experiments
4. Validate operational usefulness
5. Observe real architectural pressure
6. Only then evolve Layers and Scenarios

NOT:

1. Build perfect architecture
2. Generalize everything
3. Build engine framework
4. Then try experiments

That path is likely to collapse under complexity.

⸻

Final Note

The current state of the project is NOT failure.

The project has reached a sophisticated architectural stage where:

* domain modeling;
* operational semantics;
* spatial composition;
* and execution architecture

are beginning to collide.

This is a sign of:

* architectural maturity;
* not architectural weakness.

The correct next step is:

* controlled evolution,
* not total redesign.