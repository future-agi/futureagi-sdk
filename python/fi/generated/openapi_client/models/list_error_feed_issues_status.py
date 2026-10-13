from enum import Enum


class ListErrorFeedIssuesStatus(str, Enum):
    ACKNOWLEDGED = "acknowledged"
    ESCALATING = "escalating"
    FOR_REVIEW = "for_review"
    RESOLVED = "resolved"

    def __str__(self) -> str:
        return str(self.value)
