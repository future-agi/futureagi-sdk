from enum import Enum


class ModelHubEvalTemplatesUsageListPeriod(str, Enum):
    VALUE_0 = "30m"
    VALUE_1 = "6h"
    VALUE_2 = "1d"
    VALUE_3 = "7d"
    VALUE_4 = "30d"
    VALUE_5 = "90d"
    VALUE_6 = "180d"
    VALUE_7 = "365d"

    def __str__(self) -> str:
        return str(self.value)
