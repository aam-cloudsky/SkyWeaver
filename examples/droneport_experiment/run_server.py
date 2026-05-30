from pathlib import Path

import uvicorn

from skyweaver.api.server import SkyWeaverBackend
from skyweaver.application.dispatching.build_dispatcher import (
    build_dispatcher,
)
from skyweaver.application.runtime.application_context import (
    ApplicationContext,
)
from skyweaver.application.runtime.application_runtime import (
    ApplicationRuntime,
)
from skyweaver.core.logistics.depot import Depot

CONFIG_PATH = (Path(__file__).parent / "config.yaml").resolve()


def main() -> None:

    Depot()

    runtime = ApplicationRuntime(
        config_path=str(CONFIG_PATH),
    )

    context = ApplicationContext(
        runtime=runtime,
    )

    dispatcher = build_dispatcher(context)

    context.set_dispatcher(dispatcher)

    backend = SkyWeaverBackend()

    app = backend.create_app(context)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    main()
