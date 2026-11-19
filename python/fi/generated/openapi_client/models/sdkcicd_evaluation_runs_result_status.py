from enum import Enum


class SDKCICDEvaluationRunsResultStatus(str, Enum):
    COMPLETED = "completed"
    PROCESSING = "processing"

    def __str__(self) -> str:
        return str(self.value)
