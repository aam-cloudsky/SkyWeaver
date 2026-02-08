@dataclass(frozen=True)
class HexMouseEvent:
    coord: HexCoord
    event_type: MouseEventType
    button: MouseButton
    x: float
    y: float
