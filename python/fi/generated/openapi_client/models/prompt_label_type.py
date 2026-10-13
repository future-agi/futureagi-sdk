from enum import Enum


class PromptLabelType(str, Enum):
    CUSTOM = "custom"
    SYSTEM = "system"

    def __str__(self) -> str:
        return str(self.value)
