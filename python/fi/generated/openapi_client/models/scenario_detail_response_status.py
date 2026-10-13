from enum import Enum


class ScenarioDetailResponseStatus(str, Enum):
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"
    DELETING = "Deleting"
    EDITING = "Editing"
    ERROR = "Error"
    EXPERIMENTEVALUATION = "ExperimentEvaluation"
    FAILED = "Failed"
    INACTIVE = "Inactive"
    NOTSTARTED = "NotStarted"
    OPTIMIZATIONEVALUATION = "OptimizationEvaluation"
    PARTIALCOMPLETED = "PartialCompleted"
    PARTIALEXTRACTED = "PartialExtracted"
    PARTIALRUN = "PartialRun"
    PROCESSING = "Processing"
    QUEUED = "Queued"
    RUNNING = "Running"
    UPLOADING = "Uploading"

    def __str__(self) -> str:
        return str(self.value)
