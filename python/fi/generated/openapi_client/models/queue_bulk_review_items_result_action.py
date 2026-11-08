from enum import Enum


class QueueBulkReviewItemsResultAction(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"

    def __str__(self) -> str:
        return str(self.value)
