from enum import Enum


class AnnotationQueueAssignmentStrategy(str, Enum):
    LOAD_BALANCED = "load_balanced"
    MANUAL = "manual"
    ROUND_ROBIN = "round_robin"

    def __str__(self) -> str:
        return str(self.value)
