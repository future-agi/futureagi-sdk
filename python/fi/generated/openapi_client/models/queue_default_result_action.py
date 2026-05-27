from enum import Enum


class QueueDefaultResultAction(str, Enum):
    CREATED = "created"
    FETCHED = "fetched"
    RESTORED = "restored"

    def __str__(self) -> str:
        return str(self.value)
