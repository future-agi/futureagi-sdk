from enum import Enum


class PersonaVerbosity(str, Enum):
    BALANCED = "balanced"
    BRIEF = "brief"
    DETAILED = "detailed"

    def __str__(self) -> str:
        return str(self.value)
