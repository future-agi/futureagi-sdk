from enum import Enum


class PersonaListSlangUsage(str, Enum):
    HEAVY = "heavy"
    LIGHT = "light"
    MODERATE = "moderate"
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
