from enum import Enum


class ColumnSource(str, Enum):
    ANNOTATION_LABEL = "annotation_label"
    API_CALL = "api_call"
    CLASSIFICATION = "classification"
    CONDITIONAL = "conditional"
    EVALUATION = "evaluation"
    EVALUATION_REASON = "evaluation_reason"
    EVALUATION_TAGS = "evaluation_tags"
    EVAL_PLAYGROUND = "eval_playground"
    EXPERIMENT = "experiment"
    EXPERIMENT_EVALUATION = "experiment_evaluation"
    EXPERIMENT_EVALUATION_TAGS = "experiment_evaluation_tags"
    EXTRACTED_ENTITIES = "extracted_entities"
    EXTRACTED_JSON = "extracted_json"
    OPTIMISATION = "optimisation"
    OPTIMISATION_EVALUATION = "optimisation_evaluation"
    OPTIMISATION_EVALUATION_TAGS = "optimisation_evaluation_tags"
    OTHERS = "OTHERS"
    PYTHON_CODE = "python_code"
    RUN_PROMPT = "run_prompt"
    VECTOR_DB = "vector_db"

    def __str__(self) -> str:
        return str(self.value)
