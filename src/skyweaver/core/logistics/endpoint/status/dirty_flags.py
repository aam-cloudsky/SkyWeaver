from enum import Enum, auto


class DirtyFlag(Enum):
    CLEAN = auto()
    DIRTY = auto()
