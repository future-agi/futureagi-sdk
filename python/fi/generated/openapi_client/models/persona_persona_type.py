from enum import Enum


class PersonaPersonaType(str, Enum):
    SYSTEM = "system"
    WORKSPACE = "workspace"

    def __str__(self) -> str:
        return str(self.value)
