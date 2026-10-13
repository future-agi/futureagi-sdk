from enum import Enum


class UserAlertMonitorThresholdType(str, Enum):
    PERCENTAGE_CHANGE = "percentage_change"
    STATIC = "static"

    def __str__(self) -> str:
        return str(self.value)
