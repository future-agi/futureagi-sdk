from enum import Enum


class UserAlertMonitorLogType(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
