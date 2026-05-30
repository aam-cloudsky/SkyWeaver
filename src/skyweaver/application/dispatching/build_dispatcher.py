from skyweaver.application.dispatching.intent_dispatcher import IntentDispatcher

from skyweaver.application.handlers.add_vertiport_handler import (
    AddVertiportHandler,
)

from skyweaver.application.handlers.remove_vertiport_handler import (
    RemoveVertiportHandler,
)

from skyweaver.application.handlers.toggle_restriction_handler import (
    ToggleRestrictionHandler,
)

from skyweaver.application.intents.add_vertiport import AddVertiport

from skyweaver.application.intents.remove_vertiport import (
    RemoveVertiport,
)

from skyweaver.application.intents.toggle_restriction import (
    ToggleRestriction,
)

from skyweaver.application.runtime.application_context import (
    ApplicationContext,
)


def build_dispatcher(
    context: ApplicationContext,
) -> IntentDispatcher:

    return IntentDispatcher(
        {
            AddVertiport: AddVertiportHandler(context),
            RemoveVertiport: RemoveVertiportHandler(context),
            ToggleRestriction: ToggleRestrictionHandler(context),
        }
    )
