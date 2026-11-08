from enum import Enum


class TraceGraphDataRequestInterval(str, Enum):
    DAY = "day"
    HOUR = "hour"
    MONTH = "month"
    WEEK = "week"

    def __str__(self) -> str:
        return str(self.value)
