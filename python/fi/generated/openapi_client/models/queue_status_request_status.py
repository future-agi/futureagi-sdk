from enum import Enum


class QueueStatusRequestStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DRAFT = "draft"
    PAUSED = "paused"

    def __str__(self) -> str:
        return str(self.value)
