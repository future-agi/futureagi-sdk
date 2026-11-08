from enum import Enum


class EvalListFiltersEvalTypeItem(str, Enum):
    AGENT = "agent"
    CODE = "code"
    LLM = "llm"

    def __str__(self) -> str:
        return str(self.value)
