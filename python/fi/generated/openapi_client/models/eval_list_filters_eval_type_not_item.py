from enum import Enum


class EvalListFiltersEvalTypeNotItem(str, Enum):
    AGENT = "agent"
    CODE = "code"
    LLM = "llm"

    def __str__(self) -> str:
        return str(self.value)
