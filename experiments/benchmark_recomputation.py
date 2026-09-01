"""
Benchmark: controlled (selective) recomputation vs. full recomputation.

STATUS: written against the current SkyWeaver API, but NOT YET RUNNABLE.
It fails today with a TypeError before reaching any measurement, because
several `*Unit` classes under `src/skyweaver/units/**` instantiate their
`*Outpost()` with zero arguments, while the `Outpost` base class now
requires `bus`, `node_id`, and `logistics_id`. See CLAUDE.md ("Correção ao
achado de 2026-08-31") for the full trace and the affected files.

This script is meant to run ONLY against a disposable copy of the
SkyWeaver repository (e.g. /tmp/sw_copy2), never against the real
`SkyWeaver/` folder, per the standing rule: inspect/execute freely,
never modify the real repository.

Usage (once the bus-wiring issue is resolved):
    python3 benchmark_recomputation.py --config path/to/config.yaml --repeats 5
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# These imports assume the disposable copy is on sys.path (see __main__).
from skyweaver.application.intents.add_vertiport import AddVertiport
from skyweaver.application.intents.remove_vertiport import RemoveVertiport
from skyweaver.application.intents.toggle_restriction import ToggleRestriction
from skyweaver.application.runtime.application_runtime import ApplicationRuntime


@dataclass
class IntentTrial:
    intent_name: str
    elapsed_seconds: float
    nodes_reexecuted: int
    nodes_total: int

    @property
    def selectivity(self) -> float:
        """Fraction of the dependency graph that had to be re-triggered."""
        if self.nodes_total == 0:
            return 0.0
        return self.nodes_reexecuted / self.nodes_total


@dataclass
class BenchmarkResult:
    cold_start_seconds: list[float] = field(default_factory=list)
    selective_trials: list[IntentTrial] = field(default_factory=list)
    full_recompute_trials: list[IntentTrial] = field(default_factory=list)

    def summary(self) -> str:
        lines: list[str] = []

        lines.append("== Cold start ==")
        lines.append(
            f"  mean: {statistics.mean(self.cold_start_seconds):.4f}s  "
            f"stdev: {statistics.pstdev(self.cold_start_seconds):.4f}s  "
            f"n={len(self.cold_start_seconds)}"
        )

        for label, trials in (
            ("Selective recomputation", self.selective_trials),
            ("Full recomputation (baseline)", self.full_recompute_trials),
        ):
            lines.append(f"\n== {label} ==")
            by_intent: dict[str, list[IntentTrial]] = {}
            for t in trials:
                by_intent.setdefault(t.intent_name, []).append(t)

            for intent_name, ts in by_intent.items():
                times = [t.elapsed_seconds for t in ts]
                sels = [t.selectivity for t in ts]
                lines.append(
                    f"  {intent_name}: "
                    f"time mean={statistics.mean(times):.4f}s "
                    f"stdev={statistics.pstdev(times):.4f}s | "
                    f"nodes reexecuted/total mean={statistics.mean(sels)*100:.1f}% "
                    f"(n={len(ts)})"
                )

        if self.selective_trials and self.full_recompute_trials:
            sel_mean = statistics.mean(t.elapsed_seconds for t in self.selective_trials)
            full_mean = statistics.mean(
                t.elapsed_seconds for t in self.full_recompute_trials
            )
            if sel_mean > 0:
                lines.append(
                    f"\n== Speedup (full / selective) == {full_mean / sel_mean:.2f}x"
                )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# NOTE: the two functions below are the part that needs confirming once the
# bus-wiring issue is fixed. `count_executed_nodes` assumes the runtime
# exposes, per intent dispatch, which dependency-graph nodes were actually
# triggered (the paper's Fig. \ref{fig:dataflow} numbers this order, so the
# information should exist somewhere in ApplicationRuntime / RuntimeUnits --
# the exact attribute/hook name needs to be confirmed against the unblocked
# code, not guessed here).
# ---------------------------------------------------------------------------


def count_executed_nodes(runtime: ApplicationRuntime) -> tuple[int, int]:
    """
    Returns (nodes_reexecuted_in_last_dispatch, nodes_total_in_graph).

    PLACEHOLDER: needs to be wired to whatever the real runtime exposes for
    per-dispatch node execution counts. Not guessed/invented here.
    """
    raise NotImplementedError(
        "Needs the real hook name from ApplicationRuntime/RuntimeUnits "
        "once the bus-wiring issue is resolved."
    )


def time_call(fn: Callable[[], None]) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def run_cold_start(config_path: str) -> tuple[ApplicationRuntime, float]:
    start = time.perf_counter()
    runtime = ApplicationRuntime(config_path=config_path)
    elapsed = time.perf_counter() - start
    return runtime, elapsed


def run_selective_intent(
    runtime: ApplicationRuntime,
    intent_name: str,
    dispatch: Callable[[], None],
) -> IntentTrial:
    elapsed = time_call(dispatch)
    reexecuted, total = count_executed_nodes(runtime)
    return IntentTrial(
        intent_name=intent_name,
        elapsed_seconds=elapsed,
        nodes_reexecuted=reexecuted,
        nodes_total=total,
    )


def run_full_recompute_baseline(
    config_path: str,
    intent_name: str,
) -> IntentTrial:
    """
    Baseline: cold-start the whole runtime again instead of applying the
    intent selectively. nodes_reexecuted == nodes_total by construction.
    """
    runtime, elapsed = run_cold_start(config_path)
    _, total = count_executed_nodes(runtime)
    return IntentTrial(
        intent_name=intent_name,
        elapsed_seconds=elapsed,
        nodes_reexecuted=total,
        nodes_total=total,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()

    config_path = str(Path(args.config).resolve())

    result = BenchmarkResult()

    # --- Cold start ---
    for _ in range(args.repeats):
        _, elapsed = run_cold_start(config_path)
        result.cold_start_seconds.append(elapsed)

    # --- Selective vs. full, per intent type ---
    # Example intents; exact constructor arguments (coordinates, heliport id,
    # etc.) need to be confirmed against the case-study data once runnable.
    intent_dispatchers: dict[str, Callable[[ApplicationRuntime], Callable[[], None]]] = {
        "ToggleRestriction": lambda rt: lambda: None,  # TODO: wire real dispatch
        "AddVertiport": lambda rt: lambda: None,  # TODO: wire real dispatch
        "RemoveVertiport": lambda rt: lambda: None,  # TODO: wire real dispatch
    }

    for intent_name, make_dispatch in intent_dispatchers.items():
        for _ in range(args.repeats):
            runtime, _ = run_cold_start(config_path)
            trial = run_selective_intent(runtime, intent_name, make_dispatch(runtime))
            result.selective_trials.append(trial)

            baseline_trial = run_full_recompute_baseline(config_path, intent_name)
            result.full_recompute_trials.append(baseline_trial)

    print(result.summary())


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
    main()