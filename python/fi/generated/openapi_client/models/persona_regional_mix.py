from enum import Enum


class PersonaRegionalMix(str, Enum):
    HEAVY = "heavy"
    LIGHT = "light"
    MODERATE = "moderate"
    NONE = "none"

    def __str__(self) -> str:
        return str(self.value)
