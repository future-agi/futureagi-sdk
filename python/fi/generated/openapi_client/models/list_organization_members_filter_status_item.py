from enum import Enum


class ListOrganizationMembersFilterStatusItem(str, Enum):
    ACTIVE = "Active"
    DEACTIVATED = "Deactivated"
    EXPIRED = "Expired"
    PENDING = "Pending"

    def __str__(self) -> str:
        return str(self.value)
