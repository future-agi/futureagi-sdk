from enum import Enum


class EvalConfigResponseModel(str, Enum):
    PROTECT = "protect"
    PROTECT_FLASH = "protect_flash"
    TURING_FLASH = "turing_flash"
    TURING_LARGE = "turing_large"
    TURING_SMALL = "turing_small"

    def __str__(self) -> str:
        return str(self.value)
