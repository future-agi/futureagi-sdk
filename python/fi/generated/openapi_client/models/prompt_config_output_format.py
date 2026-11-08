from enum import Enum


class PromptConfigOutputFormat(str, Enum):
    ARRAY = "array"
    AUDIO = "audio"
    IMAGE = "image"
    NUMBER = "number"
    OBJECT = "object"
    STRING = "string"

    def __str__(self) -> str:
        return str(self.value)
