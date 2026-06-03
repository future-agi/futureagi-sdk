from enum import Enum


class CallTranscriptSpeakerRole(str, Enum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALLS = "tool_calls"
    TOOL_CALL_RESULT = "tool_call_result"
    UNKNOWN = "unknown"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)
