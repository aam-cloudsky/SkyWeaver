Application Service Architecture
# Application Layer

The `application/` package defines the operational orchestration layer of SkyWeaver.

This layer is responsible for:

- coordinating runtime execution;
- interpreting operational intents;
- dispatching actions;
- exposing runtime accessors;
- organizing explicit execution pipelines.

It is intentionally designed as a synchronous and explicitly orchestrated architecture.

---

# Architectural Philosophy

SkyWeaver does not use a fully event-driven architecture.

Instead, the system follows an:

```text
Application Service Architecture
```

where runtime execution is:

- explicit;
- deterministic;
- synchronous;
- fully traceable.

Operational stages are intentionally invoked through explicit `.run()` calls rather than implicit reactive cascades.

Example:

```python
units.routes.run()
```

instead of hidden asynchronous event propagation.

This design improves:

- reproducibility;
- debugging;
- scientific traceability;
- operational transparency;
- runtime predictability.

---

# High-Level Runtime Flow

```text
Frontend / API / CLI
        ↓
     Intents
        ↓
   IntentDispatcher
        ↓
 Application Handlers
        ↓
   Runtime Context
        ↓
 Units / Outposts
        ↓
       Depot
        ↓
 Reactive Synchronization
        ↓
 WebSocket / Frontend Projection
```

---

# Core Concepts

## RuntimeBootstrap

The `RuntimeBootstrap` is the composition root of the system.

Responsibilities:

- initialize the Depot;
- instantiate runtime units;
- execute the initialization pipeline;
- return a ready operational runtime.

It does not contain business logic.

---

## RuntimeUnits

`RuntimeUnits` is the canonical runtime container.

It owns the instantiated operational units:

- YAML loading;
- sources;
- domain construction;
- alignment;
- hexagonal discretization;
- restrictions;
- routing.

This structure centralizes runtime ownership and simplifies future scalability.

---

## ApplicationContext

The `ApplicationContext` is a runtime façade.

Responsibilities:

- expose runtime accessors;
- provide operational queries;
- coordinate runtime recomputation.

It does not bootstrap the system.

---

## Intents

Intents represent semantic operational actions.

Examples:

- `ToggleRestriction`
- `BeginDragTerminal`
- `EndDragTerminal`

An intent represents:

```text
something that should happen
```

rather than:

```text
something that already happened
```

---

## IntentDispatcher

The dispatcher maps intents into executable application handlers.

This creates a clean separation between:

- UI interactions;
- transport layers;
- operational execution.

---

# Explicit Orchestration

A fundamental design principle of SkyWeaver is:

```text
explicit orchestration over implicit automation
```

The system intentionally avoids:

- hidden side effects;
- asynchronous execution chains;
- implicit dependency propagation;
- opaque runtime mutation.

Instead, the operational pipeline remains fully visible and deterministic.

This architecture is particularly suitable for:

- scientific simulations;
- operational airspace systems;
- reproducible experiments;
- routing research;
- infrastructure planning.


"""
LEGACY APPLICATION RUNTIME

This module predates the new application-layer architecture.

It is kept temporarily as:
- operational reference;
- migration fallback;
- behavioral comparison.

Future systems should use:
- RuntimeBootstrap
- RuntimeUnits
- ApplicationContext
- IntentDispatcher
"""