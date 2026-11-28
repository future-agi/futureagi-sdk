from enum import Enum


class ScoreSourceType(str, Enum):
    CALL_EXECUTION = "call_execution"
    DATASET_ROW = "dataset_row"
    OBSERVATION_SPAN = "observation_span"
    PROTOTYPE_RUN = "prototype_run"
    TRACE = "trace"
    TRACE_SESSION = "trace_session"

    def __str__(self) -> str:
        return str(self.value)
