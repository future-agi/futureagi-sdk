from typing import Any, Dict, List, Optional

from fi.integrations.providers import ProviderModels
from fi.testcases import LLMTestCase
from fi.utils.errors import MissingRequiredConfigForEvalTemplate

model_list = ProviderModels().get_all_models()


class EvalTemplate:
    eval_id: str
    name: str
    description: str
    eval_tags: List[str]
    required_keys: List[str]
    output: str
    eval_type_id: str
    config_schema: Dict[str, Any]
    criteria: str
    choices: List[str]
    multi_choice: bool

    def __init__(self, config: Optional[Dict[str, Any]] = {}) -> None:
        self.config = config

    def __repr__(self):
        """
        Get the string representation of the evaluation template
        """
        return f"EvalTemplate(name={self.name}, description={self.description})"

    def validate_config(self, config: Dict[str, Any]):
        """
        Validate the config for the evaluation template
        """
        for key, value in self.config_schema.items():
            if key not in config:
                raise MissingRequiredConfigForEvalTemplate(key, self.name)
            else:
                if key == "model" and config[key] not in model_list:
                    raise ValueError(
                        "Model not supported, please choose from the list of supported models"
                    )

    def validate_input(self, inputs: List[LLMTestCase]):
        """
        Validate the input against the evaluation template config

        Args:
            inputs: [
                LLMTestCase(QUERY='Who is Prime Minister of India?', RESPONSE='Narendra Modi')
            ]

        Returns:
            bool: True if the input is valid, False otherwise
        """

        for key in self.required_keys:
            for test_case in inputs:
                if getattr(test_case, key) is None:
                    raise MissingRequiredConfigForEvalTemplate(key, self.name)

        return True


class ConversationCoherence(EvalTemplate):
    eval_id = "1"


class ConversationResolution(EvalTemplate):
    eval_id = "2"


class Deterministic(EvalTemplate):
    eval_id = "3"

    def validate_input(self, inputs: List[LLMTestCase]):
        for input in inputs:
            for key, value in self.config["input"].items():
                input_dict = input.model_dump()
                if value not in input_dict.keys():
                    raise ValueError(f"Input {value} not in input")


class ContentModeration(EvalTemplate):
    eval_id = "4"


class ContextAdherence(EvalTemplate):
    eval_id = "5"


class AnswerRelevance(EvalTemplate):
    eval_id = "8"


class ContextRelevance(EvalTemplate):
    eval_id = "9"


class Completeness(EvalTemplate):
    eval_id = "10"


class ContextSimilarity(EvalTemplate):
    eval_id = "13"


class PII(EvalTemplate):
    eval_id = "14"


class Toxicity(EvalTemplate):
    eval_id = "15"


class Tone(EvalTemplate):
    eval_id = "16"


class Sexist(EvalTemplate):
    eval_id = "17"


class PromptInjection(EvalTemplate):
    eval_id = "18"


class NotGibberishText(EvalTemplate):
    eval_id = "19"


class SafeForWorkText(EvalTemplate):
    eval_id = "20"


class InstructionAdherence(EvalTemplate):
    eval_id = "21"


class DataPrivacyCompliance(EvalTemplate):
    eval_id = "22"


class IsJson(EvalTemplate):
    eval_id = "23"


class EndsWith(EvalTemplate):
    eval_id = "24"


class Equals(EvalTemplate):
    eval_id = "25"


class ContainsAll(EvalTemplate):
    eval_id = "26"


class LengthLessThan(EvalTemplate):
    eval_id = "27"


class ContainsNone(EvalTemplate):
    eval_id = "28"


class Regex(EvalTemplate):
    eval_id = "29"


class StartsWith(EvalTemplate):
    eval_id = "30"


class ApiCall(EvalTemplate):
    eval_id = "31"


class LengthBetween(EvalTemplate):
    eval_id = "32"


class CustomCodeEval(EvalTemplate):
    eval_id = "34"


class LLMJudge(EvalTemplate):
    eval_id = "35"


class AgentJudge(EvalTemplate):
    eval_id = "36"


class JsonSchemeValidation(EvalTemplate):
    eval_id = "37"


class OneLine(EvalTemplate):
    eval_id = "38"


class ContainsValidLink(EvalTemplate):
    eval_id = "39"


class IsEmail(EvalTemplate):
    eval_id = "40"


class LengthGreaterThan(EvalTemplate):
    eval_id = "41"


class NoValidLinks(EvalTemplate):
    eval_id = "42"


class Contains(EvalTemplate):
    eval_id = "43"


class ContainsAny(EvalTemplate):
    eval_id = "44"


class ContextSufficiency(EvalTemplate):
    eval_id = "45"


class GradingCriteria(EvalTemplate):
    eval_id = "46"


class Groundedness(EvalTemplate):
    eval_id = "47"


class RagasAnswerCorrectness(EvalTemplate):
    eval_id = "48"


class RagasHarmfulness(EvalTemplate):
    eval_id = "49"


class RagasContextPrecision(EvalTemplate):
    eval_id = "50"


class RagasCoherence(EvalTemplate):
    eval_id = "51"


class RagasConciseness(EvalTemplate):
    eval_id = "52"


class RagasContextRecall(EvalTemplate):
    eval_id = "53"


class RagasFaithfulness(EvalTemplate):
    eval_id = "54"


class RagasContextRelevancy(EvalTemplate):
    eval_id = "55"


class SummaryAccuracy(EvalTemplate):
    eval_id = "56"


class AnswerSimilarity(EvalTemplate):
    eval_id = "57"


class Output(EvalTemplate):
    eval_id = "59"


class ContextRetrieval(EvalTemplate):
    eval_id = "60"


class Ranking(EvalTemplate):
    eval_id = "61"


class ImageInstruction(EvalTemplate):
    eval_id = "62"


class ImageInputOutput(EvalTemplate):
    eval_id = "63"


class SummaryQuality(EvalTemplate):
    eval_id = "64"


class FactualAccuracy(EvalTemplate):
    eval_id = "66"


class TranslationAccuracy(EvalTemplate):
    eval_id = "67"


class CulturalSensitivity(EvalTemplate):
    eval_id = "68"


class BiasDetection(EvalTemplate):
    eval_id = "69"


class LLMFunctionCalling(EvalTemplate):
    eval_id = "72"
