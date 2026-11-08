from enum import Enum


class AutomationRuleConditionsOperator(str, Enum):
    AND = "and"

    def __str__(self) -> str:
        return str(self.value)
