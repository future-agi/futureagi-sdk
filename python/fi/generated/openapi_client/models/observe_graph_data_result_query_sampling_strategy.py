from enum import Enum


class ObserveGraphDataResultQuerySamplingStrategy(str, Enum):
    BOUNDED_LATEST_STATE_PREFIX = "bounded_latest_state_prefix"
    NEWEST_TRACE_CANDIDATES = "newest_trace_candidates"
    TIME_STRATIFIED_LATEST_STATE = "time_stratified_latest_state"

    def __str__(self) -> str:
        return str(self.value)
