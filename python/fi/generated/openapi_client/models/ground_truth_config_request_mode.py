from enum import Enum


class GroundTruthConfigRequestMode(str, Enum):
    AUTO = "auto"
    DISABLED = "disabled"
    MANUAL = "manual"

    def __str__(self) -> str:
        return str(self.value)
