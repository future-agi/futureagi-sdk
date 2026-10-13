from enum import Enum


class SimulateExportReadType(str, Enum):
    RUNTEST = "runtest"
    TESTEXECUTION = "testexecution"

    def __str__(self) -> str:
        return str(self.value)
