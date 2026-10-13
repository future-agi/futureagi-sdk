from enum import Enum


class DatasetModelType(str, Enum):
    BINARYCLASSIFICATION = "BinaryClassification"
    GENERATIVEIMAGE = "GenerativeImage"
    GENERATIVELLM = "GenerativeLLM"
    GENERATIVEVIDEO = "GenerativeVideo"
    MULTIMODAL = "MultiModal"
    NUMERIC = "Numeric"
    OBJECTDETECTION = "ObjectDetection"
    RANKING = "Ranking"
    REGRESSION = "Regression"
    SCORECATEGORICAL = "ScoreCategorical"
    SEGMENTATION = "Segmentation"
    STT = "STT"
    TTS = "TTS"

    def __str__(self) -> str:
        return str(self.value)
