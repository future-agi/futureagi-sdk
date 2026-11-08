from enum import Enum


class TraceVoiceCallDetailResultEvalRollupScope(str, Enum):
    SPAN = "span"
    TRACE = "trace"

    def __str__(self) -> str:
        return str(self.value)
