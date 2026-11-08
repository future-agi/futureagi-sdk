from enum import Enum


class TraceVoiceCallListResponseQueryAppliedFilterVersion(str, Enum):
    CANONICAL_JSON_SHA256_V1 = "canonical-json-sha256-v1"

    def __str__(self) -> str:
        return str(self.value)
