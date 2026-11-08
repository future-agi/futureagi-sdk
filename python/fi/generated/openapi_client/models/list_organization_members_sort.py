from enum import Enum


class ListOrganizationMembersSort(str, Enum):
    CREATED_AT = "created_at"
    DATE_JOINED = "date_joined"
    EMAIL = "email"
    NAME = "name"
    ORG_LEVEL = "org_level"
    STATUS = "status"
    TYPE = "type"
    VALUE_1 = "-name"
    VALUE_11 = "-created_at"
    VALUE_13 = "-org_level"
    VALUE_3 = "-email"
    VALUE_5 = "-status"
    VALUE_7 = "-type"
    VALUE_9 = "-date_joined"

    def __str__(self) -> str:
        return str(self.value)
