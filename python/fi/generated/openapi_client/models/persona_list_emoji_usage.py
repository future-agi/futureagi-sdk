from enum import Enum


class PersonaListEmojiUsage(str, Enum):
    HEAVY = "heavy"
    LIGHT = "light"
    NEVER = "never"
    REGULAR = "regular"

    def __str__(self) -> str:
        return str(self.value)
