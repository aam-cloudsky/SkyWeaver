from skyweaver.application.handlers import intent_rules
from skyweaver.application.intents.toggle_restriction import ToggleRestriction
from skyweaver.application.runtime.application_context import ApplicationContext


class ToggleRestrictionHandler:
    """
    Toggle restrictions from frontend GIS interactions.

    A cell outside the grid, with a heliport or with a vertiport cannot be
    toggled. Otherwise the cell enters or leaves `RestrictionToggles`; the
    flow recomputes the restricted cells, the airspace graph, the routes and
    the scene.
    """

    def __init__(self, context: ApplicationContext):
        self.context = context

    def __call__(self, intent: ToggleRestriction) -> None:

        self.context.runtime.transact(
            lambda snapshot: intent_rules.toggle_restriction(
                snapshot, intent.latitude, intent.longitude
            )
        )
