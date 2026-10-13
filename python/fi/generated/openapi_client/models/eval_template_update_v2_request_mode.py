from enum import Enum


class EvalTemplateUpdateV2RequestMode(str, Enum):
    AGENT = "agent"
    AUTO = "auto"
    QUICK = "quick"

    def __str__(self) -> str:
        return str(self.value)
