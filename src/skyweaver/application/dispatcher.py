from typing import Callable


class IntentDispatcher:

    def __init__(self, services: dict[type, Callable]):
        self._services = services

    def dispatch(self, intent):
        handler = self._services.get(type(intent))
        if not handler:
            raise RuntimeError(
                f"No handler registered for {type(intent).__name__}"
            )
        handler(intent)
