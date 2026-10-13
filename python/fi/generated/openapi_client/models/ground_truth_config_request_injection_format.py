from enum import Enum


class GroundTruthConfigRequestInjectionFormat(str, Enum):
    CONVERSATIONAL = "conversational"
    STRUCTURED = "structured"
    XML = "xml"

    def __str__(self) -> str:
        return str(self.value)
