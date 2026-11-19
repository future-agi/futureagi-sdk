from enum import Enum


class ExperimentFeedbackSubmitRequestActionType(str, Enum):
    RECALCULATE_DATASET = "recalculate_dataset"
    RECALCULATE_ROW = "recalculate_row"
    RETUNE = "retune"
    RETUNE_RECALCULATE = "retune_recalculate"

    def __str__(self) -> str:
        return str(self.value)
