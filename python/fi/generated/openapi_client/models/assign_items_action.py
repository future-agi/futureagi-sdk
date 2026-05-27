from enum import Enum


class AssignItemsAction(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    SET = "set"

    def __str__(self) -> str:
        return str(self.value)
