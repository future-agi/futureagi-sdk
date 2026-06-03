from enum import Enum


class PersonaListVerbosity(str, Enum):
    BALANCED = "balanced"
    BRIEF = "brief"
    DETAILED = "detailed"

    def __str__(self) -> str:
        return str(self.value)
