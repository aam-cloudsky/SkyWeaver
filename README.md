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

### 1. Backend dependencies

```bash
poetry install
```

> **Windows note:** GeoPandas/Shapely depend on GDAL. If you hit GDAL-related install errors, the most reliable workaround is to run the commands above in a Python 3.12 environment that already has GDAL configured (e.g., the one bundled with QGIS).

### 2. Frontend dependencies

```bash
cd frontend
npm install
```

### 3. Run the system

```bash
python examples/droneport_experiment/run_system.py
```

This starts the backend runtime, the FastAPI/WebSocket server, and the frontend development server.

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
