from enum import IntEnum, auto


class TopicsEnum(IntEnum):
    DEPOT_REGISTRY = auto()
    DEPOT_GET = auto()
    DEPOT_SET = auto()
    #DEPOT = auto()
    LIFECYCLE = auto()
    NOTIFY = auto()
    DEPOT_UPDATE = auto()
    VALIDITY = auto()
