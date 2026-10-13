from enum import Enum


class CallExecutionRerunRerunType(str, Enum):
    CALL_AND_EVAL = "call_and_eval"
    EVAL_ONLY = "eval_only"

    def __str__(self) -> str:
        return str(self.value)
