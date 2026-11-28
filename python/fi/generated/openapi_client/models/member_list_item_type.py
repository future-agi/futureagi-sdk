from enum import Enum


class MemberListItemType(str, Enum):
    INVITE = "invite"
    MEMBER = "member"

    def __str__(self) -> str:
        return str(self.value)
