from enum import Enum


class ListErrorFeedIssuesSource(str, Enum):
    EVAL = "eval"
    SCANNER = "scanner"

    def __str__(self) -> str:
        return str(self.value)
