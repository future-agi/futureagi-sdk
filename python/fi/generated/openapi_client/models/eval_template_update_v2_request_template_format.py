from enum import Enum


class EvalTemplateUpdateV2RequestTemplateFormat(str, Enum):
    JINJA = "jinja"
    MUSTACHE = "mustache"

    def __str__(self) -> str:
        return str(self.value)
