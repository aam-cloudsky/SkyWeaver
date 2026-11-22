"""Record the reference scenes of the core migration (tests/reference/).

    python tools/record_reference_scenes.py                       # record
    python tools/record_reference_scenes.py --check-determinism   # record twice, compare
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

import reference_harness as harness  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check-determinism", action="store_true")
    args = parser.parse_args()

    first = harness.run_sequence()
    if args.check_determinism:
        second = harness.run_sequence()
        different = [name for name in first if first[name] != second[name]]
        if different:
            print("not deterministic:", ", ".join(different))
            return 1
        print("deterministic: two runs gave identical scenes")
        return 0

    harness.write_reference(first)
    for name, scene in first.items():
        print(name, harness.layer_summary(scene))
    observed = harness.observe_websocket_after_intent()
    harness.write_websocket_record(observed, first["00_startup"])
    print("websocket (known defect):", observed["messages_after_intent"],
          "messages after an intent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
