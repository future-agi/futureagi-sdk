from enum import IntEnum


class MemberRoleUpdateOrgLevel(IntEnum):
    VALUE_15 = 15
    VALUE_8 = 8
    VALUE_3 = 3
    VALUE_1 = 1

    def __str__(self) -> str:
        return str(self.value)
