from enum import Enum


class DatasetSource(str, Enum):
    BUILD = "build"
    DEMO = "demo"
    EXPERIMENT_SNAPSHOT = "experiment_snapshot"
    GRAPH = "graph"
    KNOWLEDGE_BASE = "knowledge_base"
    OBSERVE = "observe"
    SCENARIO = "scenario"
    SDK = "sdk"

    def __str__(self) -> str:
        return str(self.value)
