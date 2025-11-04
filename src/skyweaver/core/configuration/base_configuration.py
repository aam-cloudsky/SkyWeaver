from dataclasses import dataclass, field, fields
from typing import Dict
from skyweaver.core.bus.message_hub import MessageHub, TopicsEnum, MessageContext
from skyweaver.core.bus.reserved_id_enum import ReservedIDs

@dataclass
class BaseConfiguration:
    """Reactive configuration mixin that syncs assignments with AirspaceState."""

    _transaction_open: bool = field(default=True, init=False, repr=False)
    _publisher_id: int = field(default=-1, init=False, repr=False)

    def __post_init__(self):
        """Hook called automatically by dataclasses."""
        _publisher_id = self._message_hub_setup()

        object.__setattr__(self, "_publisher_id", _publisher_id)
        object.__setattr__(self, "_transaction_open", False)
        
    def _message_hub_setup(self):
        message_hub = MessageHub()
        _publisher_id = message_hub.register_publisher()

        message_hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_GET,
            publisher_id=_publisher_id,
            subscriber=self._on_airspace_fetch_response
        )


        message_hub.subscribe(
            topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
            publisher_id=_publisher_id,
            subscriber=self._on_airspace_pull_update
        )

        MessageHub().publish(
            topic=TopicsEnum.AIRSPACE_STATE_GET,
            message=self._dict_variables(),
            message_context=MessageContext(
                from_id=_publisher_id,
                to_id=ReservedIDs.AIRSPACE_STATE.value
            )
        )

        return _publisher_id


    def _on_airspace_fetch_response(self, message: Dict, context: MessageContext):
        """Handle initial FETCH response from AirspaceState.
        
        Config requests an updates of its fields from AirspaceState upon initialization.
        """

        for field_name, value in message.items():
            if field_name in self._dict_variables().keys():
                object.__setattr__(self, field_name, value)


    def _on_airspace_pull_update(self, message: Dict, context: MessageContext):
        """Handle incremental updates (broadcasts) from AirspaceState.
        config listens to updates from AirspaceState and applies them locally.
        """

        for field_name, value in message.items():
            if field_name in self._dict_variables().keys():
                object.__setattr__(self, field_name, value)


    def _list_variables(self):
        """Return a list of public dataclass field names."""
        variables_names = [f.name for f in fields(self) if not f.name.startswith("_")]
        # verify if publisher id is present and remove it
        if "publisher_id" in variables_names:
            variables_names.remove("publisher_id")
        return variables_names
    
    def _dict_variables(self):
        """Return a dictionary of public dataclass fields and their values."""
        variables = {f.name: getattr(self, f.name) for f in fields(self) if not f.name.startswith("_")}
        if "publisher_id" in variables:
            del variables["publisher_id"]
        return variables

    def __setattr__(self, name, value):
        """Intercepts all assignments and updates AirspaceState if needed."""

        if not getattr(self, "_transaction_open", False):
            raise AttributeError(
                "Direct assignment is disabled. Please, use the context manager: 'with Configuration() as config:'."
            )
        else:
            if name in self._list_variables():
                object.__setattr__(self, name, value)


    def __enter__(self):
        # Disable auto-sync (including __setattr__)
        object.__setattr__(self, "_transaction_open", True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Push entire configuration to AirspaceState

                if hasattr(self, "_publisher_id"):
                    MessageHub().publish(
                        topic=TopicsEnum.AIRSPACE_STATE_UPDATE,
                        message=self._dict_variables(),
                        message_context=MessageContext(
                            from_id=self._publisher_id, #type: ignore
                            to_id=ReservedIDs.AIRSPACE_STATE.value
                        )
                    )
        finally:
            object.__setattr__(self, "_transaction_open", False)

        
