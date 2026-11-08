from enum import Enum


class ApiTooLargeErrorCode(str, Enum):
    EXPORT_TOO_LARGE = "export_too_large"
    ITEMS_TOO_LARGE = "items_too_large"

    def __str__(self) -> str:
        return str(self.value)
