from enum import Enum


class CreateScoreScoreSource(str, Enum):
    API = "api"
    AUTO = "auto"
    HUMAN = "human"
    IMPORTED = "imported"

    def __str__(self) -> str:
        return str(self.value)
