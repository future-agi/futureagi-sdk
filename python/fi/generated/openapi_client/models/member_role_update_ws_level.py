from enum import IntEnum


class MemberRoleUpdateWsLevel(IntEnum):
    VALUE_8 = 8
    VALUE_3 = 3
    VALUE_1 = 1

    def __str__(self) -> str:
        return str(self.value)
