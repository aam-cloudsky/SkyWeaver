# 🛰️ SkyWeaver

A reactive architecture for urban-airspace Command-and-Control, combining a shared-state repository, an explicit dependency graph, a synchronous communication bus, and a GIS scene-projection pipeline.

This repository accompanies the paper *"SkyWeaver: A Reactive Command-and-Control Platform for Urban Airspace Planning"* (SIGE 2026), by Davi Guanabara de Aragão, Cesar Augusto Cavalheiro Marcondes, Filipe Alves Neto Verri, and Marcos R. O. A. Máximo — Autonomous Computational Systems Lab (LAB-SCA), Aeronautics Institute of Technology (ITA).

---

## What is SkyWeaver?

For a deeper explanation of the runtime architecture, GIS boundaries, scene materialization pipeline, and frontend/backend design philosophy, see:

```text
project_description.md
src/skyweaver/application/read-me.md
```

The computation runs on [Reed](https://github.com/aam-cloudsky/Reed) 2.0.0: `src/skyweaver/flow.py` declares it as a Reed flow of thirteen functions (see "🧩 Computation as a Reed flow" below).

---

## Status

SkyWeaver is an **architectural proof of concept**, not an operationally validated Command-and-Control system. It has not been evaluated with human operators, real-time traffic, or certified ATM infrastructure.

Current state:

- The backend pipeline (YAML loading, source ingestion, domain projection, hex-grid discretization, restriction handling, backbone routing) is implemented and was the basis for the recomputation experiments reported in the SIGE 2026 paper.
- The frontend renders the synchronized geospatial scene (heliports, droneports, restrictions, corridors) as a **read-only visualization**.
- Interactive UI controls for issuing intents directly from the scene (toggling restrictions, adding or removing droneports) are **under development** and not yet exposed in the frontend.

---

## Tech Stack

**Backend:** Python (≥3.12), FastAPI (WebSocket interface), GeoPandas, Shapely, igraph, PyYAML

**Frontend:** Vue 3, TypeScript, Vite, Pinia, MapLibre GL, deck.gl, Turf.js

---

## Getting Started

### Backend
- Python
- Reed (reactive flow of typed values)
- FastAPI
- GeoPandas
- Shapely
- igraph

### Frontend
- Vue 3
- Pinia
- MapLibre GL
- deck.gl
- TypeScript

---

## ▶️ Running the System

### 1️⃣ Install Python 3.12 and create a virtual environment

SkyWeaver requires Python >=3.12. The recommended way to set this up is [uv](https://docs.astral.sh/uv/):

```bash
uv python install 3.12
uv venv --python 3.12 .venv
```

### 2️⃣ Install backend dependencies

SkyWeaver depends on Reed, pinned to `git+https://github.com/aam-cloudsky/Reed.git@v2.0.0`. Your GitHub credentials must give read access to that repository while it is private.

```bash
uv pip install --python .venv/bin/python3.12 -e ".[dev]"
```

To work on Reed and SkyWeaver together, install Reed from the sibling checkout first:

```bash
uv pip install --python .venv/bin/python3.12 -e ../Reed
uv pip install --python .venv/bin/python3.12 -e ".[dev]"
```

`poetry.lock` must be regenerated with `poetry lock` after a dependency change (Render installs with `pip install -e .` and does not read it).

### 3️⃣ Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4️⃣ Run the complete system

```bash
.venv/bin/python3.12 examples/droneport_experiment/run_system.py
```

This starts the backend runtime, the FastAPI/WebSocket server, and the frontend development server.

### 5️⃣ Run the tests

```bash
.venv/bin/python3.12 -m pytest
.venv/bin/python3.12 tools/record_reference_scenes.py --check-determinism
```

The suite compares the scene after each step of a reference sequence (startup, add a vertiport, remove it, toggle a restriction, toggle it back) with the files in `tests/reference/`, recorded before the migration to Reed. GitHub Actions runs the same commands on every push (`.github/workflows/ci.yml`); while Reed is private, the repository secret `REED_READ_TOKEN` must hold a read-only token for it.

Known defect: no scene reaches the WebSocket after an intent (the intent endpoints run in a worker thread and `asyncio.create_task` fails there), so the map updates only after a reload. `test_websocket_known_defect_no_scene_after_intent` records it; the next issue fixes it.

---

## 🧩 Computation as a Reed flow

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

- reactive GIS scene streaming;
- frontend scene rendering;
- vertiport visualization;
- interactive vertiport insertion;
- selective recomputation (only the functions whose inputs changed run);
- hexagonal operational discretization;
- local projected operational runtime.

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

This keeps the frontend isolated from:

- runtime internals;
- hexagonal discretization internals;
- routing graph internals;
- local operational coordinate systems.

---

## Acknowledgments

This work was partially funded by CNPq (Grant No. 307525/2022-8) and by the National Civil Aviation Secretariat (SAC) under Grant No. TED n. 11525720240005-003882/2024, through the ITA AAM SAC INOVAAC 2 program.

---

## Contributing

This is an active research prototype maintained by a single contributor. Issues and suggestions are welcome; please open an issue before submitting a pull request.

---

## 🔥 Banner

> 🛰️ *"SkyWeaver: weaving grids, constraints, and future autonomous skies."*

---


## TODOs: 

1. Refactor the GraphBuilder to avoid code duplication and improve maintainability. The current implementation has several similar patterns that can be abstracted into helper methods or a more generic graph construction approach.
2. The class Routing could be renamed to something like RoutePlanner or RouteCalculator, to better reflect its purpose next to `compute_routes`.
