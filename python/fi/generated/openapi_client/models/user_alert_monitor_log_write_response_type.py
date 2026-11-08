from enum import Enum


class UserAlertMonitorLogWriteResponseType(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
