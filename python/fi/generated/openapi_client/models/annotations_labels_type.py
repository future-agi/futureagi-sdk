from enum import Enum


class AnnotationsLabelsType(str, Enum):
    CATEGORICAL = "categorical"
    NUMERIC = "numeric"
    STAR = "star"
    TEXT = "text"
    THUMBS_UP_DOWN = "thumbs_up_down"

    def __str__(self) -> str:
        return str(self.value)
