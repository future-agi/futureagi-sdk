from enum import Enum


class AutomationRuleConditionsFilterItemFilterConfigAttributeValueTypesItemType2Type1(
    str, Enum
):
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
