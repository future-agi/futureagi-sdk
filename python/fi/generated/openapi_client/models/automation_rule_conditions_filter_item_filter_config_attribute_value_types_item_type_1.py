from enum import Enum


class AutomationRuleConditionsFilterItemFilterConfigAttributeValueTypesItemType1(
    str, Enum
):
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
