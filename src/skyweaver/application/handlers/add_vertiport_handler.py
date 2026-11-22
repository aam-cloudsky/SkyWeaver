from skyweaver.application.handlers import intent_rules
from skyweaver.application.intents.add_vertiport import AddVertiport
from skyweaver.application.runtime.application_context import ApplicationContext


class AddVertiportHandler:
    """
    Handle frontend-driven vertiport insertion requests.

    Responsibilities:
    - receive geographic WGS84 coordinates from the application intent layer;
    - locate the hexagonal cell under the point (`intent_rules.locate`);
    - reject a cell outside the grid, with a heliport, with a vertiport or
      restricted;
    - feed the vertiport edit log with the new edit; the flow recomputes
      the vertiports, the routes and the scene.

    Spatial pipeline:
        Frontend WGS84 Coordinates
                ↓
        Domain Projection
                ↓
        Local Cartesian Space
                ↓
        Hexagonal Discretization
                ↓
        VertiportEdit("add", coord)
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def __call__(self, intent: AddVertiport) -> None:

        self.context.runtime.transact(
            lambda snapshot: intent_rules.add_vertiport(
                snapshot, intent.latitude, intent.longitude
            )
        )
