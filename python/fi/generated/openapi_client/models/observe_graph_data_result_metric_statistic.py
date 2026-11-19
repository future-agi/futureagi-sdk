from enum import Enum


class ObserveGraphDataResultMetricStatistic(str, Enum):
    COUNT = "count"
    MEAN = "mean"
    PERCENTAGE = "percentage"
    SUM = "sum"

    def __str__(self) -> str:
        return str(self.value)
