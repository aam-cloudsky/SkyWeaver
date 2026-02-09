from dataclasses import dataclass
from typing import Optional
from examples.view.hex_matplotlib_ihm import HexMouseEvent
from skyweaver.application.intent import (
    HexIntent,
    ToggleRestriction,
    BeginDragTerminal,
    EndDragTerminal,
)
from skyweaver.application.dispatcher import IntentDispatcher
from skyweaver.units.grid.geometry.hexcoord import HexCoord


class HexApplicationController:
    """
    Application layer.

    Responsibilities:
    - Interpret UI events
    - Emit domain intents
    - Hold transient interaction state

    Non-responsibilities:
    - No rendering
    - No geometry
    - No business logic execution
    """

    def __init__(self, dispatcher: IntentDispatcher):
        self.dispatcher = dispatcher
        self._drag_origin: Optional[HexCoord] = None

    def handle_mouse_event(self, event: HexMouseEvent):

        # -------------------------------
        # LEFT CLICK → modify grid
        # -------------------------------
        if event.button == "left":

            if event.event_type == "press":
                self.dispatcher.dispatch(ToggleRestriction(coord=event.coord))

        # -------------------------------
        # RIGHT CLICK → drag terminal
        # -------------------------------
        elif event.button == "right":

            if event.event_type == "press":
                self._drag_origin = event.coord
                self.dispatcher.dispatch(BeginDragTerminal(coord=event.coord))

            elif event.event_type == "release" and self._drag_origin:
                self.dispatcher.dispatch(
                    EndDragTerminal(
                        start=self._drag_origin,
                        end=event.coord,
                    )
                )
                self._drag_origin = None
