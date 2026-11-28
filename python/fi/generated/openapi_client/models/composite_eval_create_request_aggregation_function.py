from enum import Enum


class CompositeEvalCreateRequestAggregationFunction(str, Enum):
    AVG = "avg"
    MAX = "max"
    MIN = "min"
    PASS_RATE = "pass_rate"
    WEIGHTED_AVG = "weighted_avg"

    def __str__(self) -> str:
        return str(self.value)
