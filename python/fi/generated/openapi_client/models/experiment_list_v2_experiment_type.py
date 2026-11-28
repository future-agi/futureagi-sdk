from enum import Enum


class ExperimentListV2ExperimentType(str, Enum):
    IMAGE = "image"
    LLM = "llm"
    STT = "stt"
    TTS = "tts"

    def __str__(self) -> str:
        return str(self.value)
