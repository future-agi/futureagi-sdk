from enum import Enum


class EvalListFiltersTemplateTypeItem(str, Enum):
    COMPOSITE = "composite"
    SINGLE = "single"

    def __str__(self) -> str:
        return str(self.value)
