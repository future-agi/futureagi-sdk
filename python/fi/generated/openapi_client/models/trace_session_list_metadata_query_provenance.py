from enum import Enum


class TraceSessionListMetadataQueryProvenance(str, Enum):
    SPANS_PER_SESSION_CANDIDATE = "spans_per_session_candidate"

    def __str__(self) -> str:
        return str(self.value)
