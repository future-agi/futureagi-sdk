from enum import Enum


class EvalTemplateListChartsResponseResultQueryErrorCode(str, Enum):
    QUERY_FAILED = "query_failed"
    READ_BUDGET_EXCEEDED = "read_budget_exceeded"
    TEMPLATE_LIMIT_EXCEEDED = "template_limit_exceeded"

    def __str__(self) -> str:
        return str(self.value)
