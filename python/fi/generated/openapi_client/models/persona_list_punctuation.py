from enum import Enum


class PersonaListPunctuation(str, Enum):
    CLEAN = "clean"
    ERRATIC = "erratic"
    EXPRESSIVE = "expressive"
    MINIMAL = "minimal"

    def __str__(self) -> str:
        return str(self.value)
