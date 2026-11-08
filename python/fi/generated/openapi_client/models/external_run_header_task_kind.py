from enum import Enum


class ExternalRunHeaderTaskKind(str, Enum):
    EXTERNAL = "external"

    def __str__(self) -> str:
        return str(self.value)
