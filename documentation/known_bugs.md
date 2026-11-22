# Documented bugs

The bugs found while moving SkyWeaver's core to Reed (issue 6), with their status, how to reproduce them and where they were fixed. Commands run from the repository root with the environment of the README (`.venv`, `pip install -e ".[dev]"`).

| # | Bug | Area | Status |
| --- | --- | --- | --- |
| B1 | No scene reaches the WebSocket after an intent | backend, API | open (next issue) |
| B2 | The frontend shows "Offline" without `frontend/.env` | frontend | open (workaround) |
| B3 | The "Vertiport" option of the add menu does nothing | frontend | open |
| B4 | The frontend cannot remove a droneport or toggle a restriction | frontend | open |
| B5 | A rejected intent answers `200 {"status": "ok"}` | API | open |
| B6 | `run_system.py` passes `--config`, which `run_server.py` ignores | examples | open |
| B7 | Toggling a restriction takes about half a second | performance | open |
| B8 | CI cannot install Reed until the token secret exists | CI | open (configuration) |
| B9 | Routes changed between processes (memory addresses) | routing | fixed (`bc3caa4`) |
| B10 | Concurrent intents could interleave | runtime | fixed (`6b177c0`) |
| B11 | The distribution generators could not be imported | units | fixed (`70e36d0`) |
| B12 | Examples that did not run | examples | removed (`70e36d0`) |
| B13 | The recomputation experiment assumed its node count | experiments | fixed (`70e36d0`) |
| B14 | `rich<15` conflicted with Reed | dependencies | fixed (`e10973a`) |
| B15 | Stale `__pycache__` folders keep deleted packages visible | working tree | open (cleanup command) |

---

## Open

### B1. No scene reaches the WebSocket after an intent

**Symptom.** A droneport added from the map does not appear until the page is reloaded. The backend log shows, after each intent:

```text
server.py:89: RuntimeWarning: coroutine 'WebSocket.send_json' was never awaited
```

**Cause.** The intent endpoints of `src/skyweaver/api/server.py` are synchronous, so FastAPI runs them in a worker thread with no event loop. `SkyWeaverBackend._on_scene_update` calls `asyncio.create_task(websocket.send_json(...))` there; it fails and the `except Exception: pass` hides the failure. `GET /scene` is up to date, because `self._scene` is assigned before the send.

**Reproduce.**

1. `cp frontend/.env.example frontend/.env` (see B2), then `.venv/bin/python examples/droneport_experiment/run_system.py`.
2. Open http://localhost:5173, click ➕, choose "Droneport", click a free point inside the routes area.
3. Nothing appears; the log shows `POST /intent/add-vertiport ... 200 OK` and the warning above. Reload: the droneport and its route appear.

Automated: `.venv/bin/python -m pytest tests/test_reference_scenes.py -k websocket`. The test asserts that zero messages arrive after an intent; `tests/reference/websocket_known_defect.json` records the same. Confirmed by hand on macOS on 2026-11-22.

**Fix direction.** Keep the server's event loop at startup and schedule the send with `loop.call_soon_threadsafe` (or `asyncio.run_coroutine_threadsafe`). The fixing issue inverts the test (one scene after the intent, equal to `01_add_vertiport.json`). Present since before `cd02743`.

### B2. The frontend shows "Offline" without `frontend/.env`

**Symptom.** The map loads with no layers and the status badge says "Offline". The backend log shows no request from the browser.

**Cause.** Since `5140584` the frontend reads `VITE_API_BASE_URL` and `VITE_WS_BASE_URL`. Their local values are only in `frontend/.env.example`, and `.env` is ignored by git, so a fresh checkout requests `undefined/health` and `undefined/ws`.

**Reproduce.** Remove `frontend/.env` and run `run_system.py`.

**Workaround.** `cp frontend/.env.example frontend/.env`. **Fix direction.** Fall back to `http://127.0.0.1:8000` and `ws://127.0.0.1:8000` when the variables are undefined, so only Render needs them.

### B3. The "Vertiport" option of the add menu does nothing

**Cause.** `AppShell.vue` offers "Droneport" and "Vertiport", but the map click handler of `MapCanvas.vue` only acts when `activeTool === 'droneport'`.

**Reproduce.** ➕ → "Vertiport" → click the map: no request reaches the backend.

### B4. The frontend cannot remove a droneport or toggle a restriction

**Cause.** The frontend calls only `POST /intent/add-vertiport`. `remove-vertiport` and `toggle-restriction` exist in the API (and in the tests) but no button sends them; 🚫 and the ruler change no backend state.

**Reproduce.** `grep -rn "intent/" frontend/src` lists only `add-vertiport`. Through the API:

```bash
curl -s -X POST localhost:8000/intent/remove-vertiport -H 'content-type: application/json' -d '{"latitude":-22.90,"longitude":-43.40}'
curl -s -X POST localhost:8000/intent/toggle-restriction -H 'content-type: application/json' -d '{"latitude":-22.903826262966408,"longitude":-43.2654493466201}'
```

### B5. A rejected intent answers `200 {"status": "ok"}`

**Cause.** The handlers return nothing; a click outside the grid, on a heliport cell, on an existing droneport or on a restricted cell is rejected silently and the endpoint still answers `ok`. The user gets no feedback.

**Reproduce.**

```bash
curl -s -X POST localhost:8000/intent/add-vertiport -H 'content-type: application/json' -d '{"latitude":10,"longitude":10}'
```

answers `{"status":"ok"}` and the scene does not change (`tests/test_api.py::test_intent_outside_the_grid_is_accepted_and_changes_nothing` pins this behavior). `ApplicationRuntime.transact` already returns whether a value was fed; the API can expose it.

### B6. `run_system.py` passes `--config`, which `run_server.py` ignores

**Cause.** `run_system.py` starts the server with `--config <path>`; `run_server.py` has no argument parsing and always uses `examples/droneport_experiment/config.yaml`. Harmless today because both point to the same file.

**Reproduce.** Change `CONFIG_PATH` in `run_system.py` to another file: the server still loads the default one.

### B7. Toggling a restriction takes about half a second

**Cause.** `build_airspace_graph` rebuilds the graph of every domain cell on each toggle. Adding or removing a droneport does not rebuild it.

**Reproduce.** `.venv/bin/python experiments.py --repeats 3`. On the local VM: toggle about 535 ms (4 of 13 nodes), add or remove about 43 ms (3 of 13). The old core rebuilt the airspace graph on every intent.

### B8. CI cannot install Reed until the token secret exists

**Cause.** `reed-sync` is installed from `github.com/aam-cloudsky/Reed`, which needs credentials while the repository is private. `.github/workflows/ci.yml` and `render.yaml` use `REED_READ_TOKEN` when it is set.

**Reproduce.** Push the branch without the secret: the "Install package" step fails to clone Reed. **Fix.** Create a fine-grained read-only token for the Reed repository and store it as the repository secret `REED_READ_TOKEN` (and as the Render variable of the same name), or make Reed public.

### B15. Stale `__pycache__` folders keep deleted packages visible

**Cause.** Git does not track folders. Folders that held only bytecode (`src/skyweaver/core/`, `tests/flow/`, `units/*/logistics/`) stay in a working tree after their files are deleted. Nothing in them is imported; `test_architecture` checks for Python files, not folders.

**Clean.**

```bash
rm -rf src/skyweaver/core tests/flow
find src tests tools examples -type d -name __pycache__ -prune -exec rm -rf {} +
find src tests tools examples -type d -empty -delete
```

---

## Fixed

### B9. Routes changed between processes

**Cause.** Pairs of terminals were oriented by `id(a) < id(b)`, the memory address of each cell, in `Routing.build_knn_pairs`, `Routing.build_all_pairs` and `connectivity_builder._build_single_linkage_hac_pairs`, and `_build_paths` iterated over a set. The direction and order of the routes, and the choice among paths of equal cost, depended on the process (importing pytest first was enough to change them).

**Reproduce on the old code.**

```bash
SW="$(pwd)"
git worktree add /tmp/sw_cd02743 cd02743
git -C /tmp/sw_cd02743 checkout f4c0aa7 -- tests tools
cd /tmp/sw_cd02743
PYTHONPATH=src "$SW/.venv/bin/python" tools/record_reference_scenes.py --check-determinism
```

It prints `not deterministic: 00_startup, ...`, and `pytest tests/test_reference_scenes.py -k "not websocket"` fails all five steps. Remove the worktree afterwards: `cd "$SW" && git worktree remove --force /tmp/sw_cd02743`.

**Fix.** `bc3caa4`: pairs oriented by `(q, r)`, paths built in sorted pair order. `--check-determinism` runs in CI.

### B10. Concurrent intents could interleave

**Cause.** The old handlers changed the units in place from FastAPI worker threads with no lock, so two requests could interleave a read of the vertiport list and a write. Found by reading the code; not reproduced on `cd02743`.

**Fix.** `6b177c0`: one lock in `ApplicationRuntime`; every intent goes through `transact`. **Check.** `tests/test_api.py::test_concurrent_intents_lose_no_edit` sends eight intents at once; replacing the lock by a null context makes it fail.

### B11. The distribution generators could not be imported

**Cause.** `units/distributions/base_distribution.py` and `uav_mav_uav_distribution.py` imported `skyweaver.distributions...`, a package that does not exist, and wrote their points to the old depot.

**Reproduce on the old code.** In the worktree of B9: `PYTHONPATH=src "$SW/.venv/bin/python" -c "import skyweaver.units.distributions.base_distribution"` raises `ModuleNotFoundError: No module named 'skyweaver.distributions'`.

**Fix.** `70e36d0`: the generators keep their points on the instance. `test_every_module_imports` covers them.

### B12. Examples that did not run

**Cause.** `examples/clustering/clustering.py`, `grid/hexgrid.py`, `routing/graph.py`, `routing/interactive_routing_not_working.py` and `view/hex_click_toggle.py` imported packages that no longer existed; the others drove the old core.

**Fix.** Removed in `70e36d0` (list in the commit message). The SIGE 2026 version is the tag `paper-sige2026-camera-ready`.

### B13. The recomputation experiment assumed its node count

**Cause.** `experiments.py` reported `nodes_reexecuted = 1` as a constant, read from the handler source, not measured. `experiments/benchmark_recomputation.py` never ran (its own docstring says so).

**Fix.** `70e36d0`: `experiments.py` counts the nodes that start from Reed's execution trace (13 at startup; 4 for a toggle; 3 for an add or remove). The placeholder was removed.

### B14. `rich<15` conflicted with Reed

**Cause.** SkyWeaver pinned `rich (>=14.3.2,<15.0.0)`; Reed 2.0.0 requires `rich>=15.0.0`, so both could not be installed together.

**Fix.** `e10973a`: `rich (>=15.0.0,<16.0.0)`.
