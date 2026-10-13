from enum import Enum


class ListWorkspaceMembersFilterStatusItem(str, Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    PENDING = "Pending"

    def __str__(self) -> str:
        return str(self.value)
