from enum import Enum


class AgentDefinitionEditRequestAuthenticationMethod(str, Enum):
    API_KEY = "api_key"

    def __str__(self) -> str:
        return str(self.value)
