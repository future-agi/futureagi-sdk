from enum import Enum


class CompareDatasetStatsRequestStatType(str, Enum):
    EVALUATION = "evaluation"
    RUN_PROMPT = "run_prompt"

    def __str__(self) -> str:
        return str(self.value)
