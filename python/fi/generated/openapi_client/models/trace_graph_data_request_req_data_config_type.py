from enum import Enum


class TraceGraphDataRequestReqDataConfigType(str, Enum):
    ANNOTATION = "ANNOTATION"
    EVAL = "EVAL"
    SYSTEM_METRIC = "SYSTEM_METRIC"

    def __str__(self) -> str:
        return str(self.value)
