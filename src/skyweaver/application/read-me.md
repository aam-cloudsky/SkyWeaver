# Application Layer

The `application/` package connects the outside world (the HTTP and WebSocket API, scripts) to SkyWeaver's computation.

This layer is responsible for:

- owning the Reed session that computes the airspace;
- interpreting operational intents;
- applying each intent as one transaction;
- keeping the current scene and notifying its subscribers.

The computation itself is the Reed flow declared in `skyweaver/flow.py`. This layer feeds that flow and reads its values; it does not compute routes or geometry.

---

# Runtime Model

SkyWeaver's computation is a set of functions of typed, immutable values (`skyweaver/model/`). Each function declares its inputs by its parameter types and its output by its return type, and Reed (`reed-sync` 2.0.0) runs a function when its inputs change.

Execution stays explicit and deterministic:

- the dependencies are the declared types, visible in `skyweaver/flow.py`;
- in one `push()`, each function runs at most once, after every producer of its inputs (Reed's glitch freedom);
- a function returns a new value instead of changing a committed one;
- Reed's execution trace records which functions ran.

```text
ConfigPath → Configuration → SourceGeoData → Domain → HexGrid
Heliports, CandidateVertiports            (aligned to the domain)
HeliportCells                             (cells holding a heliport)
BaseVertiports                            (candidates off heliport cells)
Vertiports        ← VertiportEdits        (fed by add / remove intents)
RestrictedCells   ← RestrictionToggles    (fed by the toggle intent)
AirspaceGraphPack → Routes → SceneSnapshot
```

The functions that must react to a single changed input (`apply_vertiport_edits`, `restrict_cells`, `build_airspace_graph`, `compute_routes`, `materialize_scene`) declare `TriggerPolicy.ANY_INPUT_CHANGED`; the others keep Reed's default.

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
 ApplicationRuntime.transact(update)
        ↓
 intent_rules: snapshot → value to feed
        ↓
 Reed session: feed, push
        ↓
 SceneSnapshot
        ↓
 Subscribers (API scene, WebSocket)
```

---

# Core Concepts

## ApplicationRuntime

`ApplicationRuntime` owns the Reed session (`skyweaver.flow.start_session`).

At construction it feeds the configuration path, an empty `VertiportEdits` and an empty `RestrictionToggles`, and pushes once.

`transact(update)` applies one change under a lock:

1. `update` receives the current snapshot and returns the value to feed, or `None` to reject the intent (nothing is fed and nothing recomputes);
2. the runtime feeds the value and pushes;
3. it reads the new `SceneSnapshot` and notifies the subscribers once.

The lock serializes every use of the session, so two intents arriving on two FastAPI worker threads never interleave a snapshot read and a feed.

---

## ApplicationContext

The `ApplicationContext` is the façade used by external interfaces.

Responsibilities:

- expose the current scene and scene subscriptions;
- dispatch intents.

It does not bootstrap the system and gives no access to the flow's internals.

---

## Intents

Intents represent semantic operational actions in WGS84 coordinates:

- `AddVertiport`
- `RemoveVertiport`
- `ToggleRestriction`

An intent represents:

```text
something that should happen
```

rather than:

```text
something that already happened
```

---

## Intent rules

`handlers/intent_rules.py` decides, from a snapshot, what an intent changes:

- add a vertiport: the cell exists, holds no heliport, no vertiport, and is not restricted; the new value is `VertiportEdits` with an `add` edit appended;
- remove a vertiport: the cell exists and holds a vertiport; the new value is `VertiportEdits` with a `remove` edit appended;
- toggle a restriction: the cell exists and holds no heliport and no vertiport; the new value is `RestrictionToggles` with the cell added or removed.

The vertiport edit log is provisional: the scenario editor will replace it with a scenario document.

---

## IntentDispatcher

The dispatcher maps intents into application handlers. Each handler calls `ApplicationRuntime.transact` with its rule.

This keeps a clean separation between:

- UI interactions;
- transport layers;
- operational execution.

---

# Known defect

No scene reaches the WebSocket after an intent: the intent endpoints are synchronous and run in a worker thread, where `SkyWeaverBackend._on_scene_update` cannot call `asyncio.create_task`. `GET /scene` is up to date; the map updates after a reload. `tests/test_reference_scenes.py::test_websocket_known_defect_no_scene_after_intent` records the defect, and the issue that fixes it inverts that test.
