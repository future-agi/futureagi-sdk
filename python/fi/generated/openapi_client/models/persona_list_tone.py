from enum import Enum


class PersonaListTone(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    NEUTRAL = "neutral"

    def __str__(self) -> str:
        return str(self.value)
