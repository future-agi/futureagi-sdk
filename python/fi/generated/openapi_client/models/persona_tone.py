from enum import Enum


class PersonaTone(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    NEUTRAL = "neutral"

    def __str__(self) -> str:
        return str(self.value)
