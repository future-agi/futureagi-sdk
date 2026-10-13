from enum import Enum


class PersonaPunctuation(str, Enum):
    CLEAN = "clean"
    ERRATIC = "erratic"
    EXPRESSIVE = "expressive"
    MINIMAL = "minimal"

    def __str__(self) -> str:
        return str(self.value)
