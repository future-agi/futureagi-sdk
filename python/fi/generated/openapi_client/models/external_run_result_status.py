from enum import Enum


class ExternalRunResultStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    def __str__(self) -> str:
        return str(self.value)
