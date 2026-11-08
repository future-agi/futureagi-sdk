from enum import Enum


class ReviewItemRequestAction(str, Enum):
    APPROVE = "approve"
    COMMENT = "comment"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"

    def __str__(self) -> str:
        return str(self.value)
