from enum import Enum


class PageDepthExceededErrorCode(str, Enum):
    PAGE_DEPTH_EXCEEDED = "page_depth_exceeded"

    def __str__(self) -> str:
        return str(self.value)
