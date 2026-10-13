from enum import Enum


class AgentVersionResponseStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"
    DRAFT = "draft"

    def __str__(self) -> str:
        return str(self.value)
