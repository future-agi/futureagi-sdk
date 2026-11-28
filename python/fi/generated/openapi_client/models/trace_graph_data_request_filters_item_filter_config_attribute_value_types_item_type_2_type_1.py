from enum import Enum


class TraceGraphDataRequestFiltersItemFilterConfigAttributeValueTypesItemType2Type1(
    str, Enum
):
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
