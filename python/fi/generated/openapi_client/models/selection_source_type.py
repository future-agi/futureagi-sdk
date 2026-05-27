from enum import Enum


class SelectionSourceType(str, Enum):
    CALL_EXECUTION = "call_execution"
    OBSERVATION_SPAN = "observation_span"
    TRACE = "trace"
    TRACE_SESSION = "trace_session"

    def __str__(self) -> str:
        return str(self.value)
