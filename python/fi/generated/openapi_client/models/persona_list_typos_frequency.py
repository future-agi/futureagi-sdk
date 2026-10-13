from enum import Enum


class PersonaListTyposFrequency(str, Enum):
    FREQUENT = "frequent"
    NONE = "none"
    OCCASIONAL = "occasional"
    RARE = "rare"

    def __str__(self) -> str:
        return str(self.value)
