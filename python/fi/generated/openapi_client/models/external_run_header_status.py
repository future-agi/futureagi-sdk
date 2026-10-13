from enum import Enum


class ExternalRunHeaderStatus(str, Enum):
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DRAFT = "draft"
    FAILED = "failed"
    PARTIAL = "partial"
    QUEUED = "queued"
    RUNNING = "running"

    def __str__(self) -> str:
        return str(self.value)
