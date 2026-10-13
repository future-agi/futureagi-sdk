from enum import Enum


class AutomationRuleTriggerFrequency(str, Enum):
    DAILY = "daily"
    HOURLY = "hourly"
    MANUAL = "manual"
    MONTHLY = "monthly"
    WEEKLY = "weekly"

    def __str__(self) -> str:
        return str(self.value)
