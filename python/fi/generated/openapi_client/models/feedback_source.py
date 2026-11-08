from enum import Enum


class FeedbackSource(str, Enum):
    DATASET = "dataset"
    EVAL_PLAYGROUND = "eval_playground"
    EXPERIMENT = "experiment"
    OBSERVE = "observe"
    PROMPT = "prompt"
    SDK = "sdk"
    TRACE = "trace"

    def __str__(self) -> str:
        return str(self.value)
