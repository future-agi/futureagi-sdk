from enum import Enum


class ProjectSource(str, Enum):
    DEMO = "demo"
    PROTOTYPE = "prototype"
    SIMULATOR = "simulator"

    def __str__(self) -> str:
        return str(self.value)
