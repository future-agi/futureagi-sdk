from enum import Enum


class UserAlertMonitorListItemStatus(str, Enum):
    HEALTHY = "healthy"
    TRIGGERED = "triggered"

    def __str__(self) -> str:
        return str(self.value)
