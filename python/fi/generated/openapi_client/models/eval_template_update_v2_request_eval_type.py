from enum import Enum


class EvalTemplateUpdateV2RequestEvalType(str, Enum):
    AGENT = "agent"
    CODE = "code"
    LLM = "llm"

    def __str__(self) -> str:
        return str(self.value)
