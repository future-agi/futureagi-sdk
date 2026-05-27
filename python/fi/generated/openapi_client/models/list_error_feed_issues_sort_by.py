from enum import Enum


class ListErrorFeedIssuesSortBy(str, Enum):
    ERROR_COUNT = "error_count"
    FIRST_SEEN = "first_seen"
    LAST_SEEN = "last_seen"
    UNIQUE_TRACES = "unique_traces"

    def __str__(self) -> str:
        return str(self.value)
