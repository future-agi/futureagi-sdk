from enum import Enum


class ColumnDefinitionDataType(str, Enum):
    ARRAY = "array"
    AUDIO = "audio"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DOCUMENT = "document"
    FLOAT = "float"
    IMAGE = "image"
    IMAGES = "images"
    INTEGER = "integer"
    JSON = "json"
    OTHERS = "others"
    PERSONA = "persona"
    TEXT = "text"

    def __str__(self) -> str:
        return str(self.value)
