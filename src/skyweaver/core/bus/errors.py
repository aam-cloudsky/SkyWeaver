# skyweaver/core/bus/errors.py

# skyweaver/core/bus/errors.py

class DeliveryError(RuntimeError):
    """Raised when a synchronous message delivery fails."""

    def __str__(self) -> str:
        return (
            "\n\n"
            "══════════════════════════════════════\n"
            "❌  SKYWEAVER FATAL ERROR\n"
            "══════════════════════════════════════\n"
            "Depot is not initialized.\n"
            "Please start the Depot before anything.\n"
            "\n"
        )
