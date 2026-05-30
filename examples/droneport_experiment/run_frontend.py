from pathlib import Path
import subprocess

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def main() -> None:
    """
    Launch the Vue/MapLibre frontend development server.

    This script acts as the frontend composition root for the
    droneport experiment environment.

    Responsibilities:
    - isolate frontend bootstrapping from backend startup;
    - provide a canonical frontend runtime entrypoint;
    - standardize developer workflow for local execution.

    Notes:
    - expects the frontend dependencies to already be installed;
    - delegates execution to the frontend package manager;
    - intended primarily for development/runtime orchestration.
    """

    subprocess.run(
        ["npm", "run", "dev"],
        cwd=FRONTEND_DIR,
        check=True,
    )


if __name__ == "__main__":
    main()
