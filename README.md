# 🛰️ SkyWeaver

A reactive architecture for urban-airspace Command-and-Control, combining a shared-state repository, an explicit dependency graph, a synchronous communication bus, and a GIS scene-projection pipeline.

This repository accompanies the paper *"SkyWeaver: A Reactive Command-and-Control Platform for Urban Airspace Planning"* (SIGE 2026), by Davi Guanabara de Aragão, Cesar Augusto Cavalheiro Marcondes, Filipe Alves Neto Verri, and Marcos R. O. A. Máximo — Autonomous Computational Systems Lab (LAB-SCA), Aeronautics Institute of Technology (ITA).

---

## What is SkyWeaver?

SkyWeaver explores how a Command-and-Control platform can maintain a consistent, traceable representation of urban airspace—heliports, droneport candidates, restrictions, and routing—as that representation continuously changes. Instead of recomputing the entire operational picture on every change, SkyWeaver tracks dependencies between artifacts explicitly and re-executes only the units affected by a given mutation.

The architecture is organized around four mechanisms:

- **Dependency Management** — an explicit data-flow graph connecting producer-consumer units, so that only the subgraph affected by a change is re-executed.
- **Shared-State Synchronization** — a single authoritative repository, with nodes registering typed contracts for the state they consume, mutate, and produce.
- **Bus Coordination** — a synchronous, split-phase communication protocol that makes every request, reply, and broadcast observable and causally traceable.
- **Geospatial Scene Projection** — materializes the synchronized state into an interactive GIS scene, decoupled from the backend's internal computation.

A case study built around the Rio de Janeiro metropolitan region validates this organization: heliports (DECEA registry), droneport candidates (ABRASCE shopping centers), a Single-Linkage HAC backbone over a hexagonal navigable-airspace grid, and operational restrictions are integrated into a single runtime. A controlled-recomputation experiment shows that mutating a single intent re-executes only one of seven operational units.

The version published at SIGE 2026 implements these mechanisms in an in-tree core (Depot, Outpost, Parcel, the bus); it is the tag `paper-sige2026-camera-ready`. Since issue 6 the computation runs on [Reed](https://github.com/aam-cloudsky/Reed) 2.0.0, the dataflow engine extracted from that core: `src/skyweaver/flow.py` declares it as a Reed flow of thirteen functions (see "Computation as a Reed flow" below). On this version, adding or removing a droneport re-executes 3 of the 13 functions and toggling a restriction re-executes 4 (`experiments.py`).

For a deeper explanation of the runtime, the GIS boundaries and the scene materialization pipeline, see `src/skyweaver/application/read-me.md` and `project_description.md`.

---

## Status

SkyWeaver is an **architectural proof of concept**, not an operationally validated Command-and-Control system. It has not been evaluated with human operators, real-time traffic, or certified ATM infrastructure.

Current state:

- The backend pipeline (YAML loading, source ingestion, domain projection, hex-grid discretization, restriction handling, backbone routing) is implemented as a Reed flow and reproduces the scenes of the SIGE 2026 version (`tests/test_reference_scenes.py`).
- The frontend renders the synchronized geospatial scene (heliports, droneports, restrictions, corridors).
- Adding a droneport from the map is exposed; removing droneports and toggling restrictions are available through the API only. After an intent the map updates only on reload (known defect B1).
- Every known bug, open or fixed, is listed with the steps to reproduce it in `documentation/known_bugs.md`.

---

## Tech Stack

**Backend:** Python (≥3.12), Reed 2.0.0 (`reed-sync`), FastAPI (WebSocket interface), GeoPandas, Shapely, igraph, PyYAML

**Frontend:** Vue 3, TypeScript, Vite, Pinia, MapLibre GL, deck.gl, Turf.js

---

## Getting Started

### 1. Backend dependencies

SkyWeaver depends on Reed, pinned to `git+https://github.com/aam-cloudsky/Reed.git@v2.0.0`. Your GitHub credentials must give read access to that repository while it is private. With [uv](https://docs.astral.sh/uv/):

```bash
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
```

or, with Poetry, `poetry install`. To work on Reed and SkyWeaver together, install Reed from the sibling checkout first (`uv pip install --python .venv/bin/python -e ../Reed`).

> **Windows note:** GeoPandas/Shapely depend on GDAL. If you hit GDAL-related install errors, the most reliable workaround is to run the commands above in a Python 3.12 environment that already has GDAL configured (e.g., the one bundled with QGIS).

### 2. Frontend dependencies

```bash
cd frontend
npm install
cp .env.example .env
cd ..
```

The frontend reads the backend address from `frontend/.env`; without it the map stays "Offline" (B2).

### 3. Run the system

```bash
.venv/bin/python examples/droneport_experiment/run_system.py
```

This starts the backend runtime, the FastAPI/WebSocket server, and the frontend development server.

### 4. Run the tests

```bash
.venv/bin/python -m pytest
.venv/bin/python tools/record_reference_scenes.py --check-determinism
```

The suite compares the scene after each step of a reference sequence (startup, add a vertiport, remove it, toggle a restriction, toggle it back) with the files in `tests/reference/`, recorded before the migration to Reed. GitHub Actions runs the same commands on every push (`.github/workflows/ci.yml`); while Reed is private, the repository secret `REED_READ_TOKEN` must hold a read-only token for it.

---

## Computation as a Reed flow

Each step is a function of typed, immutable values (`src/skyweaver/model/`). Reed runs a function when its inputs change and keeps the latest value of each type.

```text
ConfigPath → Configuration → SourceGeoData → Domain → HexGrid
Heliports, CandidateVertiports            (aligned to the domain)
HeliportCells                             (cells holding a heliport)
BaseVertiports                            (candidates off heliport cells)
Vertiports        ← VertiportEdits        (fed by add / remove intents)
RestrictedCells   ← RestrictionToggles    (fed by the toggle intent)
AirspaceGraphPack → Routes → SceneSnapshot
```

`ApplicationRuntime` owns the Reed session. Each intent is one transaction under a lock: read the snapshot, decide the value to feed (`application/handlers/intent_rules.py`), feed, push, read the scene, notify subscribers.

---

## Roadmap

Planned directions (see also the Future Work section of the SIGE 2026 paper):

- Interactive frontend controls for issuing intents directly from the geospatial scene.
- Artifact versioning, so each produced artifact retains a history of prior states.
- Configurable invalidation policies (single-dependency vs. all-dependencies triggers).
- A human-in-the-loop confirmation step preceding execution.
- Persistence of complete state snapshots to construct and compare planning scenarios.
- An auditability and reproducibility mechanism built on structured provenance records.

---

## Citation

If you use this work, please cite:

```bibtex
@inproceedings{aragao2026skyweaver,
  title     = {SkyWeaver: A Reactive Command-and-Control Platform for Urban Airspace Planning},
  author    = {Aragão, Davi Guanabara de and Marcondes, Cesar Augusto Cavalheiro and Verri, Filipe Alves Neto and Máximo, Marcos R. O. A.},
  booktitle = {Proceedings of SIGE 2026},
  year      = {2026}
}
```

*(fill in volume/pages/DOI once the proceedings are indexed)*

---

## Acknowledgments

This work was partially funded by CNPq (Grant No. 307525/2022-8) and by the National Civil Aviation Secretariat (SAC) under Grant No. TED n. 11525720240005-003882/2024, through the ITA AAM SAC INOVAAC 2 program.

---

## Contributing

This is an active research prototype maintained by a single contributor. Issues and suggestions are welcome; please open an issue before submitting a pull request.

---
