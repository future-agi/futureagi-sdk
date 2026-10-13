from enum import Enum


class ProjectTraceType(str, Enum):
    EXPERIMENT = "experiment"
    OBSERVE = "observe"

    def __str__(self) -> str:
        return str(self.value)
