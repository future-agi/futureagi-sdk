from enum import Enum


class UserAlertMonitorThresholdOperator(str, Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"

    def __str__(self) -> str:
        return str(self.value)
