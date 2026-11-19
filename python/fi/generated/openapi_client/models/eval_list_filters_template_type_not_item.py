from enum import Enum


class EvalListFiltersTemplateTypeNotItem(str, Enum):
    COMPOSITE = "composite"
    SINGLE = "single"

    def __str__(self) -> str:
        return str(self.value)
