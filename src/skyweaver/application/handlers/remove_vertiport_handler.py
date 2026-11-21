from skyweaver.application.handlers import intent_rules
from skyweaver.application.intents.remove_vertiport import RemoveVertiport
from skyweaver.application.runtime.application_context import ApplicationContext


class RemoveVertiportHandler:
    """
    Remove an operational vertiport from frontend GIS interactions.

    Responsibilities:
    - receive WGS84 geographic coordinates from the application layer;
    - locate the hexagonal cell under the point (`intent_rules.locate`);
    - reject a cell outside the grid or without a vertiport;
    - feed the vertiport edit log with the removal; the flow recomputes the
      vertiports, the routes and the scene.

    Spatial pipeline:
        Frontend WGS84 Coordinates
                ↓
        Domain Projection
                ↓
        Local Cartesian Space
                ↓
        Hexagonal Cell Projection
                ↓
        VertiportEdit("remove", coord)
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def __call__(self, intent: RemoveVertiport) -> None:

        self.context.runtime.transact(
            lambda snapshot: intent_rules.remove_vertiport(
                snapshot, intent.latitude, intent.longitude
            )
        )
