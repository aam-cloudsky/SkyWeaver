from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class TraceID:
    value: UUID = field(default_factory=uuid4)

    def short(self, n: int = 4) -> str:
        return str(self.value)[-n:]

    def __str__(self) -> str:
        return f"t:{self.short()}"

    def __repr__(self):
        return f"TraceID({self.value})"
