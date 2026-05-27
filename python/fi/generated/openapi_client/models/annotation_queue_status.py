from enum import Enum


class AnnotationQueueStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DRAFT = "draft"
    PAUSED = "paused"

    def __str__(self) -> str:
        return str(self.value)
