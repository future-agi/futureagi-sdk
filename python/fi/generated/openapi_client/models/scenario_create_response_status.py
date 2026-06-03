from enum import Enum


class ScenarioCreateResponseStatus(str, Enum):
    PROCESSING = "processing"

    def __str__(self) -> str:
        return str(self.value)
