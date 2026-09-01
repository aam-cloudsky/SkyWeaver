# 🛰️ SkyWeaver

A GIS-oriented platform for experimenting with urban airspace organization, routing, droneport planning, and future autonomous aerial operations.

---

## 📚 Architecture Documentation

For a deeper explanation of the runtime architecture, synchronization model, GIS boundaries, scene materialization pipeline, and frontend/backend design philosophy, see:

```text
project_description.md
```

---

## 🌐 What is SkyWeaver?

SkyWeaver is a modular spatial platform designed to explore:

- urban airspace organization;
- droneport / vertiport planning;
- routing and operational constraints;
- reactive GIS visualization;
- future autonomous aerial operations.

The platform combines:

- a Python GIS/runtime backend;
- a reactive WebSocket scene pipeline;
- a Vue + MapLibre frontend;
- operational editing workflows.

The project is evolving toward a future platform capable of supporting:

- planning;
- simulation;
- optimization;
- operational airspace studies.

---

## 🚀 Current Status

SkyWeaver already supports:

- backend runtime bootstrap;
- GIS scene materialization;
- WebSocket scene streaming;
- frontend spatial visualization;
- interactive vertiport insertion;
- route recomputation after accepted mutations.

The system is now capable of running a full frontend/backend reactive GIS loop.

---

## 🖥️ Tech Stack

### Backend
- Python
- FastAPI
- GeoPandas
- Shapely
- NetworkX

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

```bash
uv pip install --python .venv/bin/python3.12 -e .
```

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

This launches:

- the backend runtime;
- the FastAPI server;
- the frontend development server.

---

## 🧭 Current Features

Current implemented features include:

- reactive GIS scene streaming;
- frontend scene rendering;
- vertiport visualization;
- interactive vertiport insertion;
- synchronized runtime recomputation;
- hexagonal operational discretization;
- local projected operational runtime.

---

## 🛣️ Roadmap

Planned next steps include:

- heliport rendering;
- route rendering;
- restriction / no-fly zone overlays;
- operational radius visualization;
- layer visibility controls;
- richer operational editing tools;
- optimization workflows;
- scenario editing;
- simulation orchestration.

---

## 🧠 Important Architectural Principle

The frontend operates only in WGS84 geographic coordinates.

The backend is responsible for:

```text
WGS84
    ↓
Domain Projection
    ↓
Local Continuous Space
    ↓
Hexagonal Operational Space
```

This keeps the frontend isolated from:

- runtime synchronization internals;
- hexagonal discretization internals;
- routing graph internals;
- local operational coordinate systems.

---

## 🚩 Current Direction

SkyWeaver is evolving from a GIS debugging/prototyping tool into a reactive operational spatial platform.

The project is intentionally moving toward:

- scene-based frontend rendering;
- reactive runtime propagation;
- operational GIS workflows;
- modular simulation and optimization support.

---

## 💬 How to contribute

Feel free to open issues or suggest improvements. The project is designed to be modular and highly maintainable.

---

## 🔥 Banner

> 🛰️ *"SkyWeaver: weaving grids, constraints, and future autonomous skies."*

---


## TODOs: 

1. Refactor the GraphBuilder to avoid code duplication and improve maintainability. The current implementation has several similar patterns that can be abstracted into helper methods or a more generic graph construction approach.
2. The class Routing seems a bit odd, once it Routes Unit is already called route. Maybe it should be renamed to something like RoutePlanner or RouteCalculator, to avoid confusion with the unit name and to better reflect its purpose.
3. In Grid, cluster should have. a role like optional consumed, where it is verified if exists and then consumed, instead of being mandatory. This would allow for more flexible grid configurations and better error handling when clusters are not present. THerefore, we should add Sentinels functionality to understand the diference between CONSUMED and OPTIONAL CONSUMED.
