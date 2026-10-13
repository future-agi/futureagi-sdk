from enum import Enum


class PersonaListPersonaType(str, Enum):
    SYSTEM = "system"
    WORKSPACE = "workspace"

    def __str__(self) -> str:
        return str(self.value)
