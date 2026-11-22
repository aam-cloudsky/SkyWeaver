"""
Recomputation experiment for the SIGE 2026 revision (Reviewer 1, item 1):

    "Provide minimal evidence for at least one architectural claim. [...]
     for an intent modifying an NFZ or droneport, report the recomputation
     scope (nodes re-executed vs. total nodes) and elapsed time, versus
     full recomputation. This turns 'controlled recomputation' from
     assertion into result."

What this measures, on the Reed flow of `skyweaver.flow` (13 nodes:
load_configuration, load_geodata, build_domain, align_heliports,
align_vertiports, build_grid, locate_heliport_cells,
filter_candidate_vertiports, apply_vertiport_edits, restrict_cells,
build_airspace_graph, compute_routes, materialize_scene) and the three real
frontend-facing intent handlers (src/skyweaver/application/handlers/):

  - full recompute (baseline): cold-start the whole ApplicationRuntime.
    Every node runs once. nodes_reexecuted == nodes_total == 13.

  - selective recompute (the architectural claim): starting from an
    already-initialized runtime, dispatch one intent
    (ToggleRestriction / AddVertiport / RemoveVertiport). The nodes that
    re-execute are counted from Reed's execution trace (`node_started`
    events), not assumed.

The version published at SIGE 2026 measured the old core (7 units, one
re-executed per intent); it is the tag `paper-sige2026-camera-ready`.

Each trial runs in its own subprocess (invoked with --mode trial) to get
a true cold measurement.

Usage:
    python3 experiments.py                 # runs everything, --repeats 5
    python3 experiments.py --repeats 10     # more repeats
    python3 experiments.py --mode trial --intent full               # single trial (used internally)
    python3 experiments.py --mode trial --intent toggle_restriction # single trial (used internally)
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
CONFIG_PATH = REPO_ROOT / "examples" / "droneport_experiment" / "config.yaml"

# The 13 nodes of the flow (skyweaver.flow.NODES).
TOTAL_NODES = 13

# NOTE: an earlier version of this script used a fixed probe coordinate
# (the Rio de Janeiro map center used by the frontend). That point fell
# outside the operational grid for ToggleRestriction/AddVertiport, so the
# handlers returned early (no-op) without re-running anything -- a false
# "1 node reexecuted" result that never actually touched the pipeline.
# Fixed by deriving an in-bounds, non-conflicting probe point at runtime:
# offset from an existing vertiport's local coordinates, verified against
# domain.contains_local_point() and the heliport/vertiport cell sets before
# use, then converted to WGS84 via domain.local_to_geo_coord().
PROBE_OFFSET_METERS = 3000.0


def _started(runtime, before: set[str]) -> int:
    """How many nodes started since the trace held the ids in `before`."""

    return sum(
        1
        for event in runtime.trace.events
        if event.event_type == "node_started" and event.node_execution_id not in before
    )


def _run_full_trial() -> dict:
    """Cold-starts the whole ApplicationRuntime. Every node runs once."""
    import io
    import contextlib

    sys.path.insert(0, str(SRC_DIR))
    from skyweaver.application.runtime.application_runtime import (
        ApplicationRuntime,
    )
    from skyweaver.model import Routes

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        t0 = time.perf_counter()
        runtime = ApplicationRuntime(config_path=str(CONFIG_PATH))
        elapsed = time.perf_counter() - t0

    routes = runtime.snapshot()[Routes]

    return {
        "intent": "full_recompute",
        "elapsed_seconds": elapsed,
        "nodes_reexecuted": _started(runtime, set()),
        "nodes_total": TOTAL_NODES,
        "paths_after": len(routes.routes_graph.paths),
    }


def _run_intent_trial(intent_name: str) -> dict:
    """
    Cold-starts ApplicationRuntime once (untimed setup), then dispatches
    one intent through its real handler and times only that step.
    """
    import io
    import contextlib

    sys.path.insert(0, str(SRC_DIR))
    from skyweaver.application.runtime.application_runtime import (
        ApplicationRuntime,
    )
    from skyweaver.application.runtime.application_context import (
        ApplicationContext,
    )
    from skyweaver.application.intents.toggle_restriction import (
        ToggleRestriction,
    )
    from skyweaver.application.intents.add_vertiport import AddVertiport
    from skyweaver.application.intents.remove_vertiport import (
        RemoveVertiport,
    )
    from skyweaver.application.handlers.toggle_restriction_handler import (
        ToggleRestrictionHandler,
    )
    from skyweaver.application.handlers.add_vertiport_handler import (
        AddVertiportHandler,
    )
    from skyweaver.application.handlers.remove_vertiport_handler import (
        RemoveVertiportHandler,
    )
    from skyweaver.model import HeliportCells, Routes, Vertiports
    from skyweaver.units.domain.frame.domain import Domain
    from skyweaver.units.hexgrid.structure.hexgrid import HexGrid
    from shapely.geometry import Point as ShapelyPoint

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        runtime = ApplicationRuntime(config_path=str(CONFIG_PATH))
        context = ApplicationContext(runtime=runtime)

    snapshot = runtime.snapshot()
    paths_before = len(snapshot[Routes].routes_graph.paths)
    vertiports_before = len(snapshot[Vertiports].points)

    domain = snapshot[Domain]
    grid = snapshot[HexGrid]
    vertiports = snapshot[Vertiports].points

    if not vertiports:
        return {
            "intent": intent_name,
            "elapsed_seconds": None,
            "nodes_reexecuted": None,
            "nodes_total": TOTAL_NODES,
            "error": "no vertiports available",
        }

    if intent_name in ("toggle_restriction", "add_vertiport"):
        # Derive an in-bounds, non-conflicting probe point at runtime by
        # offsetting from an existing vertiport's local coordinates, and
        # verify it clears the same checks the real handlers apply
        # (domain bounds, heliport cell, vertiport cell) before using it.
        heliport_cells = snapshot[HeliportCells].coords
        vertiport_cells = {c.coord for c in grid.get_cell_from_cartesians(vertiports)}
        base = vertiports[0]
        probe_local = None
        for dx, dy in (
            (PROBE_OFFSET_METERS, PROBE_OFFSET_METERS),
            (-PROBE_OFFSET_METERS, PROBE_OFFSET_METERS),
            (PROBE_OFFSET_METERS, -PROBE_OFFSET_METERS),
            (-PROBE_OFFSET_METERS, -PROBE_OFFSET_METERS),
            (2 * PROBE_OFFSET_METERS, 0.0),
        ):
            candidate = ShapelyPoint(base.x + dx, base.y + dy)
            if not domain.contains_local_point(candidate):
                continue
            cell = grid.get_cell_from_cartesian(candidate)
            if (
                cell is None
                or cell.coord in heliport_cells
                or cell.coord in vertiport_cells
            ):
                continue
            probe_local = candidate
            break
        if probe_local is None:
            return {
                "intent": intent_name,
                "elapsed_seconds": None,
                "nodes_reexecuted": None,
                "nodes_total": TOTAL_NODES,
                "error": "no valid in-bounds, non-conflicting probe point found",
            }
        # local_to_geo_coord() returns coordinates in the domain's projected
        # CRS (metric), not WGS84 -- reproject before building the intent.
        geo_gdf = domain.local_to_geo_coord([probe_local]).to_crs("EPSG:4326")
        lon, lat = geo_gdf.geometry.iloc[0].x, geo_gdf.geometry.iloc[0].y

        if intent_name == "toggle_restriction":
            handler = ToggleRestrictionHandler(context)
            intent = ToggleRestriction(latitude=lat, longitude=lon)
        else:
            handler = AddVertiportHandler(context)
            intent = AddVertiport(latitude=lat, longitude=lon)
    elif intent_name == "remove_vertiport":
        # Remove a vertiport that is guaranteed to exist: the first one
        # of the case-study dataset, converted back to WGS84.
        geo_gdf = domain.local_to_geo_coord([vertiports[0]]).to_crs("EPSG:4326")
        lon, lat = geo_gdf.geometry.iloc[0].x, geo_gdf.geometry.iloc[0].y
        handler = RemoveVertiportHandler(context)
        intent = RemoveVertiport(latitude=lat, longitude=lon)
    else:
        raise ValueError(f"Unknown intent: {intent_name}")

    before = {event.node_execution_id for event in runtime.trace.events}
    with contextlib.redirect_stdout(buf):
        t0 = time.perf_counter()
        handler(intent)
        elapsed = time.perf_counter() - t0

    snapshot = runtime.snapshot()

    return {
        "intent": intent_name,
        "elapsed_seconds": elapsed,
        "nodes_reexecuted": _started(runtime, before),
        "nodes_total": TOTAL_NODES,
        "paths_before": paths_before,
        "paths_after": len(snapshot[Routes].routes_graph.paths),
        "vertiports_before": vertiports_before,
        "vertiports_after": len(snapshot[Vertiports].points),
    }


def run_trial(mode_args: argparse.Namespace) -> dict:
    if mode_args.intent == "full":
        return _run_full_trial()
    return _run_intent_trial(mode_args.intent)


def run_subprocess_trial(intent: str) -> dict:
    """Runs one trial in a fresh subprocess and parses its JSON result."""
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--mode",
            "trial",
            "--intent",
            intent,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Trial subprocess failed for intent={intent!r}:\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
    # The trial prints exactly one JSON line as its last line of stdout.
    last_line = result.stdout.strip().splitlines()[-1]
    return json.loads(last_line)


def summarize(label: str, trials: list[dict]) -> None:
    times = [t["elapsed_seconds"] for t in trials if t["elapsed_seconds"] is not None]
    if not times:
        print(f"{label}: no successful trials")
        return

    mean = statistics.mean(times)
    stdev = statistics.pstdev(times) if len(times) > 1 else 0.0
    nodes_reexecuted = trials[0]["nodes_reexecuted"]
    nodes_total = trials[0]["nodes_total"]
    selectivity = nodes_reexecuted / nodes_total * 100

    print(
        f"{label:22s} | n={len(times):2d} | "
        f"time mean={mean * 1000:7.2f}ms stdev={stdev * 1000:6.2f}ms | "
        f"nodes {nodes_reexecuted}/{nodes_total} ({selectivity:5.1f}%)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["trial", "full"],
        default="full",
        help="'trial' runs a single measurement and prints JSON (used "
        "internally, one subprocess per repeat). 'full' (default) runs "
        "the whole experiment: --repeats trials per condition, "
        "subprocess-isolated, then prints a summary.",
    )
    parser.add_argument(
        "--intent",
        choices=["full", "toggle_restriction", "add_vertiport", "remove_vertiport"],
        default="full",
        help="Only used with --mode trial.",
    )
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    if args.mode == "trial":
        result = run_trial(args)
        print(json.dumps(result))
        return

    conditions = ["full", "toggle_restriction", "add_vertiport", "remove_vertiport"]
    all_results: dict[str, list[dict]] = {c: [] for c in conditions}

    for condition in conditions:
        for _ in range(args.repeats):
            all_results[condition].append(run_subprocess_trial(condition))

    print()
    print("Recomputation scope and elapsed time, per intent")
    print("=" * 90)
    summarize("Full recompute", all_results["full"])
    summarize("ToggleRestriction", all_results["toggle_restriction"])
    summarize("AddVertiport", all_results["add_vertiport"])
    summarize("RemoveVertiport", all_results["remove_vertiport"])
    print()

    full_mean = statistics.mean(
        t["elapsed_seconds"] for t in all_results["full"]
    )
    for condition in conditions[1:]:
        times = [
            t["elapsed_seconds"]
            for t in all_results[condition]
            if t["elapsed_seconds"] is not None
        ]
        if not times:
            continue
        selective_mean = statistics.mean(times)
        speedup = full_mean / selective_mean if selective_mean > 0 else float("inf")
        print(
            f"Speedup vs. full recompute ({condition}): {speedup:.1f}x "
            f"({all_results[condition][0]['nodes_reexecuted']}/{TOTAL_NODES} nodes re-executed)"
        )

    with open(REPO_ROOT / "experiments" / "recomputation_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print(
        f"\nRaw results written to "
        f"{REPO_ROOT / 'experiments' / 'recomputation_results.json'}"
    )


if __name__ == "__main__":
    main()
