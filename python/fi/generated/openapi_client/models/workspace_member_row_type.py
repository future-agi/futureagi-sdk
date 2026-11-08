from enum import Enum


class WorkspaceMemberRowType(str, Enum):
    INVITE = "invite"
    MEMBER = "member"

    def __str__(self) -> str:
        return str(self.value)
