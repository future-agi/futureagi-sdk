from enum import Enum


class EvalTemplateCreateV2RequestTemplateFormat(str, Enum):
    JINJA = "jinja"
    MUSTACHE = "mustache"

    def __str__(self) -> str:
        return str(self.value)
