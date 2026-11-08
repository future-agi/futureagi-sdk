from enum import Enum


class CompositeEvalUpdateRequestCompositeChildAxis(str, Enum):
    CHOICES = "choices"
    CODE = "code"
    PASS_FAIL = "pass_fail"
    PERCENTAGE = "percentage"
    VALUE_0 = ""

    def __str__(self) -> str:
        return str(self.value)
