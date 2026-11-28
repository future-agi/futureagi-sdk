from enum import Enum


class DatasetLimitCheckFailedErrorCode(str, Enum):
    DATASET_LIMIT_CHECK_FAILED = "dataset_limit_check_failed"

    def __str__(self) -> str:
        return str(self.value)
