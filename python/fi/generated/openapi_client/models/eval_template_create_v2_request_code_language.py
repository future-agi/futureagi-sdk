from enum import Enum


class EvalTemplateCreateV2RequestCodeLanguage(str, Enum):
    JAVASCRIPT = "javascript"
    PYTHON = "python"

    def __str__(self) -> str:
        return str(self.value)
