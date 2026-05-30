from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.request import urlopen
from urllib.error import URLError

ROOT_DIR = Path(__file__).resolve().parents[2]

SERVER_SCRIPT = ROOT_DIR / "examples" / "droneport_experiment" / "run_server.py"

FRONTEND_SCRIPT = ROOT_DIR / "examples" / "droneport_experiment" / "run_frontend.py"


BACKEND_HEALTHCHECK_URL = "http://127.0.0.1:8000/health"

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


class SystemRuntime:
    """
    Orchestrates the complete local SkyWeaver runtime environment.

    Responsibilities:
    - launch the backend runtime server;
    - wait until the backend becomes operational;
    - launch the frontend runtime;
    - coordinate process lifecycle management;
    - gracefully terminate all subprocesses on shutdown.

    Runtime topology:

        System Runtime
            ├── Backend Runtime
            └── Frontend Runtime

    Notes:
    - intended primarily for development and local experimentation;
    - assumes frontend dependencies were already installed;
    - backend and frontend remain isolated runtimes coordinated
      by this orchestration layer.
    """

    def __init__(self):

        self._backend_process: subprocess.Popen | None = None
        self._frontend_process: subprocess.Popen | None = None

    # ======================================================
    # Public API
    # ======================================================

    def run(self) -> None:

        try:
            self._start_backend()
            self._wait_for_backend()
            self._start_frontend()

            self._wait_forever()

        except KeyboardInterrupt:
            print("\n[SkyWeaver] Shutdown requested")

        finally:
            self._shutdown()

    # ======================================================
    # Backend
    # ======================================================

    def _start_backend(self) -> None:

        print("[SkyWeaver] Starting backend runtime...")

        self._backend_process = subprocess.Popen(
            [
                sys.executable,
                str(SERVER_SCRIPT),
                "--config",
                str(CONFIG_PATH),
            ],
            cwd=ROOT_DIR,
        )

    def _wait_for_backend(self) -> None:

        print("[SkyWeaver] Waiting for backend healthcheck...")

        while True:

            try:
                with urlopen(BACKEND_HEALTHCHECK_URL) as response:

                    if response.status == 200:
                        break

            except URLError:
                pass

            time.sleep(0.5)

        print("[SkyWeaver] Backend is ready")

    # ======================================================
    # Frontend
    # ======================================================

    def _start_frontend(self) -> None:

        print("[SkyWeaver] Starting frontend runtime...")

        self._frontend_process = subprocess.Popen(
            [sys.executable, str(FRONTEND_SCRIPT)],
            cwd=ROOT_DIR,
        )

    # ======================================================
    # Lifecycle
    # ======================================================

    def _wait_forever(self) -> None:

        while True:
            time.sleep(1)

    def _shutdown(self) -> None:

        print("[SkyWeaver] Shutting down runtimes...")

        self._terminate_process(self._frontend_process)
        self._terminate_process(self._backend_process)

    def _terminate_process(
        self,
        process: subprocess.Popen | None,
    ) -> None:

        if process is None:
            return

        if process.poll() is not None:
            return

        process.send_signal(signal.SIGTERM)

        try:
            process.wait(timeout=5)

        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":

    runtime = SystemRuntime()
    runtime.run()
