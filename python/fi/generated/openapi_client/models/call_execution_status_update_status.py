from enum import Enum


class CallExecutionStatusUpdateStatus(str, Enum):
    ANALYZING = "analyzing"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"
    ONGOING = "ongoing"
    PENDING = "pending"
    QUEUED = "queued"

    def __str__(self) -> str:
        return str(self.value)
