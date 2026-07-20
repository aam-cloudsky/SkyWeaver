from dataclasses import dataclass
from enum import Enum, auto


class PropagationPolicy(Enum):

    ANY_DEPENDENCY_CHANGED = auto()
    ALL_DEPENDENCIES_CHANGED = auto()
    MANUAL = auto()
