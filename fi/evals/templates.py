from typing import Any, Dict, List, Optional

from fi.evals.types import EvalTags, RequiredKeys
from fi.integrations.providers import ProviderModels
from fi.testcases import LLMTestCase
from fi.utils.errors import MissingRequiredKeyForEvalTemplate

model_list = ProviderModels().get_all_models()


class EvalTemplate:
    name: str
    description: str
    eval_tags: List[str]
    required_keys: List[str]
    output: str
    eval_type_id: str
    config_schema: Dict[str, Any]

    def __init__(self, config: Optional[Dict[str, Any]] = {}) -> None:
        self.validate_config(config)
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
                raise MissingRequiredKeyForEvalTemplate(key, self.name)
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
                    raise MissingRequiredKeyForEvalTemplate(key, self.name)

        return True


# Specific evaluation classes
class PromptInjection(EvalTemplate):
    name = "PromptInjection"
    description = "Evaluates text for potential prompt injection attempts"
    eval_tags = [EvalTags.safety.value, EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "PromptInjection"
    config_schema = {}


class OpenAiContentModeration(EvalTemplate):
    name = "OpenAiContentModeration"
    description = "Uses OpenAI's content moderation to evaluate text safety"
    eval_tags = [EvalTags.safety.value, EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "OpenAiContentModeration"
    config_schema = {}


class PiiDetection(EvalTemplate):
    name = "PiiDetection"
    description = "Detects personally identifiable information (PII) in text"
    eval_tags = [EvalTags.safety.value, EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "PiiDetection"
    config_schema = {}


class NotGibberishText(EvalTemplate):
    name = "NotGibberishText"
    description = "Checks if the text is not gibberish"
    eval_tags = [EvalTags.safety.value, EvalTags.function.value]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "NotGibberishText"
    config_schema = {}


class SafeForWorkText(EvalTemplate):
    name = "SafeForWorkText"
    description = "Evaluates if the text is safe for work"
    eval_tags = [EvalTags.safety.value, EvalTags.function.value]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "SafeForWorkText"
    config_schema = {}


class IsJson(EvalTemplate):
    name = "IsJson"
    description = "Checks if the input is valid JSON"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "IsJson"
    config_schema = {}


class EndsWith(EvalTemplate):
    name = "EndsWith"
    description = "Checks if the text ends with a specific substring"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "EndsWith"
    config_schema = {
        "case_sensitive": {"type": "boolean", "default": True},
        "substring": {"type": "string", "default": None},
    }


class Equals(EvalTemplate):
    name = "Equals"
    description = "Checks if two texts are equal"
    eval_tags = [EvalTags.function.value]
    required_keys = [
        RequiredKeys.text.value,
        RequiredKeys.expected_response.value,
    ]
    output = "Pass/Fail"
    eval_type_id = "Equals"
    config_schema = {"case_sensitive": {"type": "boolean", "default": True}}


class ContainsAll(EvalTemplate):
    name = "ContainsAll"
    description = "Checks if the text contains all specified keywords"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsAll"
    config_schema = {
        "case_sensitive": {"type": "boolean", "default": True},
        "keywords": {"type": "list", "default": []},
    }


class LengthLessThan(EvalTemplate):
    name = "Length Less Than"
    description = "Checks if the text length is less than a specified value"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "LengthLessThan"
    config_schema = {"max_length": {"type": "integer", "default": None}}


class ContainsLink(EvalTemplate):
    name = "Contains Link"
    description = "Checks if the text contains a URL"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsLink"
    config_schema = {}


class ContainsNone(EvalTemplate):
    name = "Contains None"
    description = "Checks if the text contains none of the specified keywords"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsNone"
    config_schema = {
        "case_sensitive": {"type": "boolean", "default": True},
        "keywords": {"type": "list", "default": []},
    }


class Regex(EvalTemplate):
    name = "Regex"
    description = "Checks if the text matches a specified regex pattern"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "Regex"
    config_schema = {"pattern": {"type": "string", "default": None}}


class StartsWith(EvalTemplate):
    name = "Starts With"
    description = "Checks if the text starts with a specific substring"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "StartsWith"
    config_schema = {
        "substring": {"type": "string", "default": None},
        "case_sensitive": {"type": "boolean", "default": True},
    }


class ApiCall(EvalTemplate):
    name = "API Call"
    description = "Makes an API call and evaluates the response"
    eval_tags = [EvalTags.function.value, EvalTags.custom.value]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "ApiCall"
    config_schema = {
        "url": {"type": "string", "default": None},
        "payload": {"type": "dict", "default": {}},
        "headers": {"type": "dict", "default": {}},
    }


class LengthBetween(EvalTemplate):
    name = "Length Between"
    description = "Checks if the text length is between specified min and max values"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "LengthBetween"
    config_schema = {
        "max_length": {"type": "integer", "default": None},
        "min_length": {"type": "integer", "default": None},
    }


class JsonValidation(EvalTemplate):
    name = "Json Validation"
    description = "Validates JSON against specified criteria"
    eval_tags = [EvalTags.function.value]
    required_keys = [
        RequiredKeys.actual_json.value,
        RequiredKeys.expected_json.value,
    ]
    output = "Pass/Fail"
    eval_type_id = "JsonValidation"
    config_schema = {"validations": {"type": "list", "default": []}}


class CustomCodeEval(EvalTemplate):
    name = "CustomCodeEval"
    description = "Executes custom Python code for evaluation"
    eval_tags = [EvalTags.function.value, EvalTags.custom.value]
    required_keys = []
    output = "Pass/Fail"
    eval_type_id = "CustomCodeEval"
    config_schema = {"code": {"type": "code", "default": None}}


class CustomPrompt(EvalTemplate):
    name = "CustomPrompt"
    description = "Evaluates using a custom prompt with a specified LLM"
    eval_tags = [EvalTags.llm.value, EvalTags.custom.value]
    required_keys = []
    output = "reason"
    eval_type_id = "CustomPrompt"
    config_schema = {
        "model": {"type": "option", "default": None},
        "eval_prompt": {"type": "prompt", "default": None},
        "system_prompt": {"type": "prompt", "default": None},
    }


class JsonSchema(EvalTemplate):
    name = "JsonSchema"
    description = "Validates JSON against a specified schema"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.actual_json.value]
    output = "Pass/Fail"
    eval_type_id = "JsonSchema"
    config_schema = {"schema": {"type": "json", "default": {}}}


class OneLine(EvalTemplate):
    name = "OneLine"
    description = "Checks if the text is a single line"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "OneLine"
    config_schema = {}


class ContainsValidLink(EvalTemplate):
    name = "ContainsValidLink"
    description = "Checks if the text contains a valid URL"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsValidLink"
    config_schema = {}


class ContainsEmail(EvalTemplate):
    name = "ContainsEmail"
    description = "Checks if the text contains an email address"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsEmail"
    config_schema = {}


class IsEmail(EvalTemplate):
    name = "IsEmail"
    description = "Checks if the text is a valid email address"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "IsEmail"
    config_schema = {}


class LengthGreaterThan(EvalTemplate):
    name = "LengthGreaterThan"
    description = "Checks if the text length is greater than a specified value"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "LengthGreaterThan"
    config_schema = {"min_length": {"type": "integer", "default": None}}


class NoInvalidLinks(EvalTemplate):
    name = "NoInvalidLinks"
    description = "Checks if the text contains no invalid URLs"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "NoInvalidLinks"
    config_schema = {}


class Contains(EvalTemplate):
    name = "Contains"
    description = "Checks if the text contains a specific keyword"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "Contains"
    config_schema = {
        "keyword": {"type": "string", "default": None},
        "case_sensitive": {"type": "boolean", "default": True},
    }


class ContainsAny(EvalTemplate):
    name = "ContainsAny"
    description = "Checks if the text contains any of the specified keywords"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsAny"
    config_schema = {
        "keywords": {"type": "list", "default": []},
        "case_sensitive": {"type": "boolean", "default": True},
    }


class ContainsJson(EvalTemplate):
    name = "ContainsJson"
    description = "Checks if the text contains valid JSON"
    eval_tags = [EvalTags.function.value]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsJson"
    config_schema = {}


class ContextSufficiency(EvalTemplate):
    name = "Context Sufficiency"
    description = (
        "Evaluates if the context contains enough information to answer the " "query"
    )
    eval_tags = [EvalTags.llm.value]
    required_keys = [RequiredKeys.query.value, RequiredKeys.context.value]
    output = "Pass/Fail"
    eval_type_id = "ContextContainsEnoughInformation"
    config_schema = {"model": {"type": "option", "default": None}}


class AnswerCompleteness(EvalTemplate):
    name = "Answer Completeness"
    description = "Evaluates if the response completely answers the query"
    eval_tags = [EvalTags.llm.value]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.query.value,
    ]
    output = "Pass/Fail"
    eval_type_id = "DoesResponseAnswerQuery"
    config_schema = {"model": {"type": "option", "default": None}}


class GradingCriteria(EvalTemplate):
    name = "Grading Criteria"
    description = "Evaluates the response based on custom grading criteria"
    eval_tags = [EvalTags.llm.value, EvalTags.custom.value]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "GradingCriteria"
    config_schema = {
        "grading_criteria": {"type": "string", "default": None},
        "model": {"type": "option", "default": None},
    }


class Groundedness(EvalTemplate):
    name = "Groundedness"
    description = "Evaluates if the response is grounded in the provided context"
    eval_tags = [EvalTags.llm.value]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.context.value,
    ]
    output = "Pass/Fail"
    eval_type_id = "Groundedness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasAnswerCorrectness(EvalTemplate):
    name = "Ragas Answer Correctness"
    description = "Evaluates the correctness of the answer using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.response.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasAnswerCorrectness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasAnswerRelevancy(EvalTemplate):
    name = "Ragas Answer Relevancy"
    description = "Evaluates the relevancy of the answer to the query using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasAnswerRelevancy"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasContextRelevancy(EvalTemplate):
    name = "Ragas Context Relevancy"
    description = "Evaluates the relevancy of the context to the query using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [RequiredKeys.context.value, RequiredKeys.query.value]
    output = "score"
    eval_type_id = "RagasContextRelevancy"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasMaliciousness(EvalTemplate):
    name = "Ragas Maliciousness"
    description = "Evaluates the maliciousness of the response using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasMaliciousness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasAnswerSemanticSimilarity(EvalTemplate):
    name = "Ragas Answer Semantic Similarity"
    description = (
        "Evaluates the semantic similarity between the response and expected "
        "response using Ragas"
    )
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.expected_response.value,
    ]
    output = "score"
    eval_type_id = "RagasAnswerSemanticSimilarity"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasHarmfulness(EvalTemplate):
    name = "Ragas Harmfulness"
    description = "Evaluates the harmfulness of the response using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasHarmfulness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasContextPrecision(EvalTemplate):
    name = "Ragas Context Precision"
    description = (
        "Evaluates the precision of the context in relation to the expected "
        "response using Ragas"
    )
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasContextPrecision"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasCoherence(EvalTemplate):
    name = "Ragas Coherence"
    description = "Evaluates the coherence of the response using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasCoherence"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasConciseness(EvalTemplate):
    name = "Ragas Conciseness"
    description = "Evaluates the conciseness of the response using Ragas"
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasConciseness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasContextRecall(EvalTemplate):
    name = "Ragas Context Recall"
    description = (
        "Evaluates the recall of the context in relation to the expected response "
        "using Ragas"
    )
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasContextRecall"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasFaithfulness(EvalTemplate):
    name = "Ragas Faithfulness"
    description = (
        "Evaluates the faithfulness of the response to the context using Ragas"
    )
    eval_tags = [EvalTags.llm.value, EvalTags.ragas.value]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasFaithfulness"
    config_schema = {"model": {"type": "option", "default": None}}


class ResponseFaithfulness(EvalTemplate):
    name = "Response Faithfulness"
    description = "Evaluates if the response is faithful to the provided context"
    eval_tags = [EvalTags.llm.value]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.context.value,
    ]
    output = "Pass/Fail"
    eval_type_id = "Faithfulness"
    config_schema = {"model": {"type": "option", "default": None}}


class SummarizationAccuracy(EvalTemplate):
    name = "Summarization Accuracy"
    description = (
        "Evaluates the accuracy of a summary compared to the original document"
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.document.value,
        RequiredKeys.response.value,
    ]
    output = "Pass/Fail"
    eval_type_id = "SummaryAccuracy"
    config_schema = {"model": {"type": "option", "default": None}}


class AnswerSimilarity(EvalTemplate):
    name = "Answer Similarity"
    description = "Evaluates the similarity between the expected and actual responses"
    eval_tags = [EvalTags.grounded.value]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.response.value,
    ]
    output = "score"
    eval_type_id = "AnswerSimilarity"
    config_schema = {
        "comparator": {"type": "option", "default": None},
        "failure_threshold": {"type": "float", "default": None},
    }


class ContextSimilarity(EvalTemplate):
    name = "Context Similarity"
    description = "Evaluates the similarity between the context and the response"
    eval_tags = [EvalTags.grounded.value]
    required_keys = [
        RequiredKeys.context.value,
        RequiredKeys.response.value,
    ]
    output = "score"
    eval_type_id = "ContextSimilarity"
    config_schema = {
        "comparator": {"type": "option", "default": None},
        "failure_threshold": {"type": "float", "default": None},
    }


class EvalOutput(EvalTemplate):
    name = "Eval Output"
    description = "Scores linkage between input and output based on specified criteria"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class CheckHallucination(EvalTemplate):
    name = "Check Hallucination"
    description = "Checks if the output is hallucinated"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class ContextEvaluator(EvalTemplate):
    name = "Eval Context"
    description = "Scores how well context generates output based on specified criteria"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    output = "score"
    eval_type_id = "ContextEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class RankingEvaluator(EvalTemplate):
    name = "Eval Ranking"
    description = "Provides ranking score for each context based on specified criteria"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.context.value,
    ]
    output = "score"
    eval_type_id = "RankingEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class ImageInstruction(EvalTemplate):
    name = "Eval Image Instruction"
    description = "Scores image-instruction linkage based on specified criteria"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.image_url.value,
    ]
    output = "score"
    eval_type_id = "ImageInstructionEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class PromptEffectiveness(EvalTemplate):
    name = "Eval Prompt"
    description = (
        "Scores prompt effectiveness in generating output based on specified "
        "criteria"
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.prompt.value,
    ]
    output = "score"
    eval_type_id = "PromptEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class ImageInputAndInstruction(EvalTemplate):
    name = "Eval Image Input and Instruction"
    description = "Scores linkage between instruction, input image, and output image"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.input_image_url.value,
        RequiredKeys.output_image_url.value,
    ]
    output = "score"
    eval_type_id = "ImageInputOutputEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class SummaryQuality(EvalTemplate):
    name = "Summary Quality"
    description = (
        "Evaluates if a summary effectively captures the main points, maintains "
        "factual accuracy, and achieves appropriate length while preserving the "
        "original meaning. Checks for both inclusion of key information and "
        "exclusion of unnecessary details."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class PromptAdherence(EvalTemplate):
    name = "Prompt Adherence"
    description = (
        "Assesses how closely the output follows the given prompt instructions, "
        "checking for completion of all requested tasks and adherence to specified "
        "constraints or formats. Evaluates both explicit and implicit requirements "
        "in the prompt."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.prompt.value,
    ]
    output = "score"
    eval_type_id = "PromptEvaluator"
    config_schema = {}


class FactualAccuracy(EvalTemplate):
    name = "Factual Accuracy"
    description = (
        "Verifies the truthfulness and accuracy of statements in the output "
        "against provided reference materials or known facts. Identifies potential "
        "misrepresentations, outdated information, or incorrect assertions."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class StyleConsistency(EvalTemplate):
    name = "Style Consistency"
    description = (
        "Evaluates consistency in tone, voice, and writing style throughout the "
        "output. Checks for maintaining appropriate formality level, technical "
        "vocabulary usage, and adherence to specified style guidelines."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class TranslationAccuracy(EvalTemplate):
    name = "Translation Accuracy"
    description = (
        "Evaluates the quality of translation by checking semantic accuracy, "
        "cultural appropriateness, and preservation of original meaning. Considers "
        "both literal accuracy and natural expression in the target language."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class CulturalSensitivity(EvalTemplate):
    name = "Cultural Sensitivity"
    description = (
        "Analyzes output for cultural appropriateness, inclusive language, "
        "and awareness of cultural nuances. Identifies potential cultural "
        "biases or insensitive content."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class BiasDetection(EvalTemplate):
    name = "Bias Detection"
    description = (
        "Identifies various forms of bias including gender, racial, cultural, "
        "or ideological bias in the output. Evaluates for balanced perspective "
        "and neutral language use."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class ReasoningChain(EvalTemplate):
    name = "Reasoning Chain"
    description = (
        "Evaluates the logical flow and coherence of reasoning in the output. "
        "Checks for clear progression of ideas, valid logical connections, and "
        "sound conclusion derivation."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class UserExperienceImpact(EvalTemplate):
    name = "User Experience Impact"
    description = (
        "Assesses how well the output meets user experience goals, including "
        "clarity, accessibility, user-friendliness, and alignment with user needs "
        "and expectations."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class LegalCompliance(EvalTemplate):
    name = "Legal Compliance"
    description = (
        "Evaluates content for compliance with legal requirements, regulatory "
        "standards, and industry-specific regulations. Identifies potential legal "
        "risks and compliance violations."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class BrandVoiceConsistency(EvalTemplate):
    name = "Brand Voice Consistency"
    description = (
        "Assesses adherence to brand guidelines, tone of voice, messaging "
        "consistency, and brand value alignment in marketing or communication "
        "content."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class EducationalValue(EvalTemplate):
    name = "Educational Value"
    description = (
        "Evaluates content for educational effectiveness, including clarity of "
        "explanations, appropriate difficulty level, learning objective alignment, "
        "and pedagogical soundness."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class APIDocumentationQuality(EvalTemplate):
    name = "API Documentation Quality"
    description = (
        "Assesses the completeness and clarity of API documentation, including "
        "endpoint descriptions, parameter explanations, example usage, error handling, "
        "and response formats."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class DataPrivacyCompliance(EvalTemplate):
    name = "Data Privacy Compliance"
    description = (
        "Checks output for compliance with data privacy regulations (GDPR, HIPAA, "
        "etc.). Identifies potential privacy violations, sensitive data exposure, "
        "and adherence to privacy principles."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class MathematicalAccuracy(EvalTemplate):
    name = "Mathematical Accuracy"
    description = (
        "Validates mathematical calculations, formulas, and numerical reasoning in "
        "the output. Checks for computational accuracy and proper use of mathematical "
        "notation."
    )
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = [RequiredKeys.input.value, RequiredKeys.output.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {}


class DeterministicEvaluation(EvalTemplate):
    name = "Deterministic Evaluation"
    description = "Evaluates if the output is deterministic or not"
    eval_tags = [EvalTags.llm.value, EvalTags.futureagi.value]
    required_keys = []
    output = "choices"
    eval_type_id = "DeterministicEvaluator"
    config_schema = {
        "multi_choice": {"type": "boolean", "default": False},
        "choices": {"type": "choices", "default": []},
        "rule_prompt": {"type": "rule_prompt", "default": ""},
        "input": {"type": "rule_string", "default": []},
    }

    def validate_input(self, inputs: List[LLMTestCase]):
        for input in inputs:
            for key, value in self.config["input"].items():
                input_dict = input.model_dump()
                if value not in input_dict.keys():
                    raise ValueError(f"Input {value} not in input")
