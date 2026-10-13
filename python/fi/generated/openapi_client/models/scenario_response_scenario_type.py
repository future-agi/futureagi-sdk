from enum import Enum


class ScenarioResponseScenarioType(str, Enum):
    DATASET = "dataset"
    GRAPH = "graph"
    SCRIPT = "script"

    def __str__(self) -> str:
        return str(self.value)
