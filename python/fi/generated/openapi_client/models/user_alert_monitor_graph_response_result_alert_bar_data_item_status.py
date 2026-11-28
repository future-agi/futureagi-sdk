from enum import Enum


class UserAlertMonitorGraphResponseResultAlertBarDataItemStatus(str, Enum):
    CRITICAL = "critical"
    HEALTHY = "healthy"
    INSUFFICIENT_DATA = "insufficient_data"
    WARNING = "warning"

    def __str__(self) -> str:
        return str(self.value)
