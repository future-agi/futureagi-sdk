from enum import Enum


class ListWorkspaceMembersSort(str, Enum):
    CREATED_AT = "created_at"
    DATE_JOINED = "date_joined"
    EMAIL = "email"
    NAME = "name"
    STATUS = "status"
    TYPE = "type"
    VALUE_1 = "-name"
    VALUE_11 = "-created_at"
    VALUE_13 = "-ws_level"
    VALUE_3 = "-email"
    VALUE_5 = "-status"
    VALUE_7 = "-type"
    VALUE_9 = "-date_joined"
    WS_LEVEL = "ws_level"

    def __str__(self) -> str:
        return str(self.value)
