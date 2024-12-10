from typing import Any, Dict, List, Optional

from fi.evals.types import EvalTags, RequiredKeys
from fi.integrations.providers import ProviderModels
from fi.testcases import LLMTestCase
from fi.utils.errors import MissingRequiredKeyForEvalTemplate

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


class ConversationCoherence(EvalTemplate):
    eval_id = "1"
    name = "ConversationCoherence"
    description = (
        "Evaluates if a conversation flows logically and maintains context throughout"
    )
    eval_tags = [EvalTags.CONVERSATION]
    required_keys = [RequiredKeys.messages.value]
    output = "score"
    eval_type_id = "ConversationCoherence"
    config_schema = {"model": {"type": "option", "default": None}}


class ConversationResolution(EvalTemplate):
    eval_id = "2"
    name = "ConversationResolution"
    description = (
        "Checks if the conversation reaches a satisfactory conclusion or resolution"
    )
    eval_tags = [EvalTags.CONVERSATION]
    required_keys = [RequiredKeys.messages.value]
    output = "score"
    eval_type_id = "ConversationResolution"
    config_schema = {"model": {"type": "option", "default": None}}


class Deterministic(EvalTemplate):
    eval_id = "3"
    name = "DeterministicEvaluator"
    description = "Evaluates if the output is deterministic or not"
    eval_tags = [
        EvalTags.CUSTOM,
        EvalTags.IMAGE,
        EvalTags.LLMS,
        EvalTags.TEXT,
        EvalTags.CONVERSATION,
        EvalTags.FUTURE_EVALS,
    ]
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


class ContentModeration(EvalTemplate):
    eval_id = "4"
    name = "Content Moderation"
    description = "Uses OpenAI's content moderation to evaluate text safety"
    eval_tags = [EvalTags.SAFETY, EvalTags.TEXT]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "OpenAiContentModeration"
    config_schema = {}


class ContextAdherence(EvalTemplate):
    eval_id = "5"
    name = "Context Adherence"
    description = "Measures how well responses stay within the provided context"
    eval_tags = [EvalTags.HALLUCINATION, EvalTags.RAG, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.input.value, RequiredKeys.context.value]
    output = "score"
    eval_type_id = "ContextEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class Correctness(EvalTemplate):
    eval_id = "6"
    name = "Correctness"
    description = "Evaluates the factual accuracy of responses"
    eval_tags = [EvalTags.HALLUCINATION, EvalTags.LLMS]
    required_keys = [
        RequiredKeys.context.value,
        RequiredKeys.input.value,
        RequiredKeys.output.value,
    ]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"model": {"type": "option", "default": None}}


class PromptPerplexity(EvalTemplate):
    eval_id = "7"
    name = "Prompt Perplexity"
    description = (
        "Measures how well the model understands and processes the input prompt"
    )
    eval_tags = [EvalTags.HALLUCINATION, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.prompt.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "PromptEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class AnswerRelevance(EvalTemplate):
    eval_id = "8"
    name = "Answer Relevance"
    description = "Evaluates if answers are relevant to the given question"
    eval_tags = [EvalTags.HALLUCINATION]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasAnswerRelevancy"
    config_schema = {"model": {"type": "option", "default": None}}


class ContextRelevance(EvalTemplate):
    eval_id = "9"
    name = "Context Relevance"
    description = "Evaluates the relevancy of the context to the query"
    eval_tags = [EvalTags.RAG, EvalTags.LLMS]
    required_keys = [RequiredKeys.context.value, RequiredKeys.query.value]
    output = "score"
    eval_type_id = "RagasContextRelevancy"
    config_schema = {"model": {"type": "option", "default": None}}


class Completeness(EvalTemplate):
    eval_id = "10"
    name = "Completeness"
    description = "Evaluates if the response completely answers the query"
    eval_tags = [EvalTags.RAG, EvalTags.LLMS]
    required_keys = [RequiredKeys.response.value, RequiredKeys.query.value]
    output = "Pass/Fail"
    eval_type_id = "DoesResponseAnswerQuery"
    config_schema = {"model": {"type": "option", "default": None}}


class ChunkAttribution(EvalTemplate):
    eval_id = "11"
    name = "Chunk Attribution"
    description = "Tracks which context chunks are used in generating responses"
    eval_tags = [EvalTags.RAG, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.context.value,
        RequiredKeys.output.value,
    ]
    optional_keys = [RequiredKeys.input.value, RequiredKeys.context.value]
    output = "score"
    eval_type_id = "ContextEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class ChunkUtilization(EvalTemplate):
    eval_id = "12"
    name = "Chunk Utilization"
    description = "Measures how effectively context chunks are used in responses"
    eval_tags = [EvalTags.RAG, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.context.value,
        RequiredKeys.output.value,
    ]
    optional_keys = [RequiredKeys.input.value, RequiredKeys.context.value]
    output = "score"
    eval_type_id = "ContextEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class ContextSimilarity(EvalTemplate):
    eval_id = "13"
    name = "Context Similarity"
    description = "Compares similarity between provided and expected context"
    eval_tags = [EvalTags.RAG]
    required_keys = [RequiredKeys.context.value, RequiredKeys.response.value]
    output = "score"
    eval_type_id = "ContextSimilarity"
    config_schema = {
        "comparator": {"type": "option", "default": None},
        "failure_threshold": {"type": "float", "default": None},
    }


class PII(EvalTemplate):
    eval_id = "14"
    name = "PII"
    description = "Detects personally identifiable information (PII) in text"
    eval_tags = [EvalTags.SAFETY]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "PiiDetection"
    config_schema = {}


class Toxicity(EvalTemplate):
    eval_id = "15"
    name = "Toxicity"
    description = "Evaluates content for toxic or harmful language"
    eval_tags = [EvalTags.SAFETY, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "Pass/Fail"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class Tone(EvalTemplate):
    eval_id = "16"
    name = "Tone"
    description = "Analyzes the tone and sentiment of content"
    eval_tags = [EvalTags.SAFETY, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "Pass/Fail"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class Sexist(EvalTemplate):
    eval_id = "17"
    name = "Sexist"
    description = "Detects sexist content and gender bias"
    eval_tags = [EvalTags.SAFETY, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "Pass/Fail"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class PromptInjection(EvalTemplate):
    eval_id = "18"
    name = "Prompt Injection"
    description = "Evaluates text for potential prompt injection attempts"
    eval_tags = [EvalTags.SAFETY]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "PromptInjection"
    config_schema = {}


class NotGibberishText(EvalTemplate):
    eval_id = "19"
    name = "Not Gibberish text"
    description = "Checks if the text is not gibberish"
    eval_tags = [EvalTags.SAFETY]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "NotGibberishText"
    config_schema = {}


class SafeForWorkText(EvalTemplate):
    eval_id = "20"
    name = "Safe for Work text"
    description = "Evaluates if the text is safe for work"
    eval_tags = [EvalTags.SAFETY]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "SafeForWorkText"
    config_schema = {}


class InstructionAdherence(EvalTemplate):
    eval_id = "21"
    name = "instruction_adherence"
    description = "Assesses how closely the output follows the given prompt instructions, checking for completion of all requested tasks and adherence to specified constraints or formats. Evaluates both explicit and implicit requirements in the prompt."
    eval_tags = [EvalTags.HALLUCINATION, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.prompt.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "PromptEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class DataPrivacyCompliance(EvalTemplate):
    eval_id = "22"
    name = "Data Privacy Compliance"
    description = "Checks output for compliance with data privacy regulations (GDPR, HIPAA, etc.). Identifies potential privacy violations, sensitive data exposure, and adherence to privacy principles."
    eval_tags = [
        EvalTags.HALLUCINATION,
        EvalTags.FUTURE_EVALS,
        EvalTags.SAFETY,
        EvalTags.TEXT,
    ]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.input.value, RequiredKeys.context.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class IsJson(EvalTemplate):
    eval_id = "23"
    name = "Is Json"
    description = "Validates if content is proper JSON format"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "IsJson"
    config_schema = {}


class EndsWith(EvalTemplate):
    eval_id = "24"
    name = "Ends With"
    description = "Checks if text ends with specific substring"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "EndsWith"
    config_schema = {
        "case_sensitive": {"type": "boolean", "default": True},
        "substring": {"type": "string", "default": None},
    }


class Equals(EvalTemplate):
    eval_id = "25"
    name = "Equals"
    description = "Compares if two texts are exactly equal"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value, RequiredKeys.expected_text.value]
    output = "Pass/Fail"
    eval_type_id = "Equals"
    config_schema = {"case_sensitive": {"type": "boolean", "default": True}}


class ContainsAll(EvalTemplate):
    eval_id = "26"
    name = "Contains All"
    description = "Verifies text contains all specified keywords"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsAll"
    config_schema = {
        "case_sensitive": {"type": "boolean", "default": True},
        "keywords": {"type": "list", "default": []},
    }


class LengthLessThan(EvalTemplate):
    eval_id = "27"
    name = "Length Less Than"
    description = "Checks if text length is below threshold"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "LengthLessThan"
    config_schema = {"max_length": {"type": "integer", "default": None}}


class ContainsNone(EvalTemplate):
    eval_id = "28"
    name = "Contains None"
    description = "Verifies text contains none of specified terms"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsNone"
    config_schema = {
        "case_sensitive": {"type": "boolean", "default": True},
        "keywords": {"type": "list", "default": []},
    }


class Regex(EvalTemplate):
    eval_id = "29"
    name = "Regex"
    description = "Checks if the text matches a specified regex pattern"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "Regex"
    config_schema = {"pattern": {"type": "string", "default": None}}


class StartsWith(EvalTemplate):
    eval_id = "30"
    name = "Starts with"
    description = "Checks if text begins with specific substring"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "StartsWith"
    config_schema = {
        "substring": {"type": "string", "default": None},
        "case_sensitive": {"type": "boolean", "default": True},
    }


class ApiCall(EvalTemplate):
    eval_id = "31"
    name = "API Call"
    description = "Makes an API call and evaluates the response"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "ApiCall"
    config_schema = {
        "url": {"type": "string", "default": None},
        "payload": {"type": "dict", "default": {}},
        "headers": {"type": "dict", "default": {}},
    }


class LengthBetween(EvalTemplate):
    eval_id = "32"
    name = "Length Between"
    description = "Checks if the text length is between specified min and max values"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "LengthBetween"
    config_schema = {
        "max_length": {"type": "integer", "default": None},
        "min_length": {"type": "integer", "default": None},
    }


class JsonValidation(EvalTemplate):
    eval_id = "33"
    name = "Json Validation"
    description = "Validates JSON against specified criteria"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.actual_json.value, RequiredKeys.expected_json.value]
    output = "Pass/Fail"
    eval_type_id = "JsonValidation"
    config_schema = {"validations": {"type": "list", "default": []}}


class CustomCodeEval(EvalTemplate):
    eval_id = "34"
    name = "Custom Code Evaluation"
    description = "Executes custom Python code for evaluation"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = []
    output = "Pass/Fail"
    eval_type_id = "CustomCodeEval"
    config_schema = {"code": {"type": "code", "default": None}}


class CustomPrompt(EvalTemplate):
    eval_id = "35"
    name = "LLM as a judge"
    description = "Uses language models to evaluate content"
    eval_tags = [EvalTags.CUSTOM]
    required_keys = []
    output = "reason"
    eval_type_id = "CustomPrompt"
    config_schema = {
        "model": {"type": "option", "default": None},
        "eval_prompt": {"type": "prompt", "default": None},
        "system_prompt": {"type": "prompt", "default": None},
    }


class AgentJudge(EvalTemplate):
    eval_id = "36"
    name = "Agent as a Judge"
    description = "Uses AI agents for content evaluation"
    eval_tags = [EvalTags.CUSTOM]
    required_keys = []
    output = "reason"
    eval_type_id = "CustomPrompt"
    config_schema = {
        "model": {"type": "option", "default": None},
        "eval_prompt": {"type": "prompt", "default": None},
        "system_prompt": {"type": "prompt", "default": None},
    }


class JsonSchemeValidation(EvalTemplate):
    eval_id = "37"
    name = "Json Scheme Validation"
    description = "Validates JSON against specified criteria"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.actual_json.value, RequiredKeys.expected_json.value]
    output = "Pass/Fail"
    eval_type_id = "JsonValidation"
    config_schema = {"validations": {"type": "list", "default": []}}


class OneLine(EvalTemplate):
    eval_id = "38"
    name = "One Line"
    description = "Checks if the text is a single line"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "OneLine"
    config_schema = {}


class ContainsValidLink(EvalTemplate):
    eval_id = "39"
    name = "Contains Valid Link"
    description = "Checks for presence of valid URLs"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsValidLink"
    config_schema = {}


class IsEmail(EvalTemplate):
    eval_id = "40"
    name = "Is Email"
    description = "Validates email address format"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "IsEmail"
    config_schema = {}


class LengthGreaterThan(EvalTemplate):
    eval_id = "41"
    name = "Length Greater than"
    description = "Checks if the text length is greater than a specified value"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "LengthGreaterThan"
    config_schema = {"min_length": {"type": "integer", "default": None}}


class NoInvalidLinks(EvalTemplate):
    eval_id = "42"
    name = "No Valid Links"
    description = "Checks if the text contains no invalid URLs"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "NoInvalidLinks"
    config_schema = {}


class Contains(EvalTemplate):
    eval_id = "43"
    name = "Contains"
    description = "Checks if the text contains a specific keyword"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "Contains"
    config_schema = {
        "keyword": {"type": "string", "default": None},
        "case_sensitive": {"type": "boolean", "default": True},
    }


class ContainsAny(EvalTemplate):
    eval_id = "44"
    name = "Contains Any"
    description = "Checks if the text contains any of the specified keywords"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.text.value]
    output = "Pass/Fail"
    eval_type_id = "ContainsAny"
    config_schema = {
        "keywords": {"type": "list", "default": []},
        "case_sensitive": {"type": "boolean", "default": True},
    }


class ContextSufficiency(EvalTemplate):
    eval_id = "45"
    name = "Context Sufficieny"
    description = (
        "Evaluates if the context contains enough information to answer the query"
    )
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.query.value, RequiredKeys.context.value]
    output = "Pass/Fail"
    eval_type_id = "ContextContainsEnoughInformation"
    config_schema = {"model": {"type": "option", "default": None}}


class GradingCriteria(EvalTemplate):
    eval_id = "46"
    name = "Grading Criteria"
    description = "Evaluates the response based on custom grading criteria"
    eval_tags = [EvalTags.CUSTOM, EvalTags.LLMS]
    required_keys = [RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "GradingCriteria"
    config_schema = {
        "grading_criteria": {"type": "string", "default": None},
        "model": {"type": "option", "default": None},
    }


class Groundedness(EvalTemplate):
    eval_id = "47"
    name = "Groundedness"
    description = "Evaluates if the response is grounded in the provided context"
    eval_tags = [EvalTags.RAG, EvalTags.LLMS]
    required_keys = [RequiredKeys.response.value, RequiredKeys.context.value]
    output = "Pass/Fail"
    eval_type_id = "Groundedness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasAnswerCorrectness(EvalTemplate):
    eval_id = "48"
    name = "Ragas Answer Correctness"
    description = "Evaluates the correctness of the answer using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.response.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasAnswerCorrectness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasHarmfulness(EvalTemplate):
    eval_id = "49"
    name = "Ragas Harmfulness"
    description = "Evaluates the harmfulness of the response using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasHarmfulness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasContextPrecision(EvalTemplate):
    eval_id = "50"
    name = "Ragas Context Precision"
    description = "Evaluates the precision of the context in relation to the expected response using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasContextPrecision"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasCoherence(EvalTemplate):
    eval_id = "51"
    name = "Ragas Coherence"
    description = "Evaluates the coherence of the response using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasCoherence"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasConciseness(EvalTemplate):
    eval_id = "52"
    name = "Ragas Conciseness"
    description = "Evaluates the conciseness of the response using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [RequiredKeys.response.value]
    output = "score"
    eval_type_id = "RagasConciseness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasContextRecall(EvalTemplate):
    eval_id = "53"
    name = "Ragas Context Recall"
    description = "Evaluates the recall of the context in relation to the expected response using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [
        RequiredKeys.expected_response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasContextRecall"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasFaithfulness(EvalTemplate):
    eval_id = "54"
    name = "Response Faithfulness"
    description = (
        "Evaluates the faithfulness of the response to the context using Ragas"
    )
    eval_tags = [EvalTags.RAG]
    required_keys = [
        RequiredKeys.response.value,
        RequiredKeys.context.value,
        RequiredKeys.query.value,
    ]
    output = "score"
    eval_type_id = "RagasFaithfulness"
    config_schema = {"model": {"type": "option", "default": None}}


class RagasContextRelevancy(EvalTemplate):
    eval_id = "55"
    name = "Ragas Context Relevance"
    description = "Evaluates the relevancy of the context to the query using Ragas"
    eval_tags = [EvalTags.RAG]
    required_keys = [RequiredKeys.context.value, RequiredKeys.query.value]
    output = "score"
    eval_type_id = "RagasContextRelevancy"
    config_schema = {"model": {"type": "option", "default": None}}


class SummaryAccuracy(EvalTemplate):
    eval_id = "56"
    name = "Summarization Accuracy"
    description = (
        "Evaluates the accuracy of a summary compared to the original document"
    )
    eval_tags = [EvalTags.RAG, EvalTags.LLMS]
    required_keys = [RequiredKeys.document.value, RequiredKeys.response.value]
    output = "Pass/Fail"
    eval_type_id = "SummaryAccuracy"
    config_schema = {"model": {"type": "option", "default": None}}


class AnswerSimilarity(EvalTemplate):
    eval_id = "57"
    name = "Answer Similarity"
    description = "Evaluates the similarity between the expected and actual responses"
    eval_tags = [EvalTags.FUNCTION]
    required_keys = [RequiredKeys.expected_response.value, RequiredKeys.response.value]
    output = "score"
    eval_type_id = "AnswerSimilarity"
    config_schema = {
        "comparator": {"type": "option", "default": None},
        "failure_threshold": {"type": "float", "default": None},
    }


class Output(EvalTemplate):
    eval_id = "59"
    name = "Eval Output"
    description = "Scores linkage between input and output based on specified criteria"
    eval_tags = [EvalTags.FUTURE_EVALS, EvalTags.CUSTOM]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {
        "criteria": {"type": "string", "default": None},
        "check_internet": {"type": "boolean", "default": False},
    }


class ContextRetrieval(EvalTemplate):
    eval_id = "60"
    name = "Eval Context Retrieval Quality"
    description = "Assesses quality of retrieved context"
    eval_tags = [EvalTags.RAG, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.input.value, RequiredKeys.context.value]
    output = "score"
    eval_type_id = "ContextEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class Ranking(EvalTemplate):
    eval_id = "61"
    name = "Eval Ranking"
    description = "Provides ranking score for each context based on specified criteria"
    eval_tags = [EvalTags.RAG, EvalTags.FUTURE_EVALS]
    required_keys = [RequiredKeys.input.value, RequiredKeys.context.value]
    output = "score"
    eval_type_id = "RankingEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class ImageInstruction(EvalTemplate):
    eval_id = "62"
    name = "Eval Image Instruction (text to image)"
    description = "Scores image-instruction linkage based on specified criteria"
    eval_tags = [EvalTags.IMAGE, EvalTags.HALLUCINATION, EvalTags.FUTURE_EVALS]
    required_keys = [RequiredKeys.input.value, RequiredKeys.image_url.value]
    output = "score"
    eval_type_id = "ImageInstructionEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class ImageInputOutput(EvalTemplate):
    eval_id = "63"
    name = "Eval Image Input (s), Instruction and Output (Image Generation)"
    description = "Scores linkage between instruction, input image, and output image"
    eval_tags = [EvalTags.IMAGE, EvalTags.HALLUCINATION, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.input_image_url.value,
        RequiredKeys.output_image_url.value,
    ]
    output = "score"
    eval_type_id = "ImageInputOutputEvaluator"
    config_schema = {"criteria": {"type": "string", "default": None}}


class SummaryQuality(EvalTemplate):
    eval_id = "64"
    name = "Summary Qulity"
    description = "Evaluates if a summary effectively captures the main points, maintains factual accuracy, and achieves appropriate length while preserving the original meaning. Checks for both inclusion of key information and exclusion of unnecessary details."
    eval_tags = [EvalTags.TEXT, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class PromptAdherence(EvalTemplate):
    eval_id = "65"
    name = "Prompt Adherence"
    description = "Assesses how closely the output follows the given prompt instructions, checking for completion of all requested tasks and adherence to specified constraints or formats. Evaluates both explicit and implicit requirements in the prompt."
    eval_tags = [EvalTags.TEXT, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.prompt.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "PromptEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class FactualAccuracy(EvalTemplate):
    eval_id = "66"
    name = "Factual Accuracy"
    description = "Verifies the truthfulness and accuracy of statements in the output against provided reference materials or known facts. Identifies potential misrepresentations, outdated information, or incorrect assertions."
    eval_tags = [EvalTags.TEXT, EvalTags.LLMS, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": True}}


class TranslationAccuracy(EvalTemplate):
    eval_id = "67"
    name = "Translation Accuracy"
    description = "Evaluates the quality of translation by checking semantic accuracy, cultural appropriateness, and preservation of original meaning. Considers both literal accuracy and natural expression in the target language."
    eval_tags = [EvalTags.TEXT, EvalTags.FUTURE_EVALS, EvalTags.LLMS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class CulturalSensitivity(EvalTemplate):
    eval_id = "68"
    name = "Cultural Sensitivity"
    description = "Analyzes output for cultural appropriateness, inclusive language, and awareness of cultural nuances. Identifies potential cultural biases or insensitive content."
    eval_tags = [EvalTags.LLMS, EvalTags.IMAGE, EvalTags.FUTURE_EVALS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class BiasDetection(EvalTemplate):
    eval_id = "69"
    name = "Bias Detection"
    description = "Identifies various forms of bias including gender, racial, cultural, or ideological bias in the output. Evaluates for balanced perspective and neutral language use."
    eval_tags = [
        EvalTags.FUTURE_EVALS,
        EvalTags.TEXT,
        EvalTags.LLMS,
        EvalTags.HALLUCINATION,
    ]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class ReasoningChain(EvalTemplate):
    eval_id = "70"
    name = "Reasoning Chain"
    description = "Evaluates the logical flow and coherence of reasoning in the output. Checks for clear progression of ideas, valid logical connections, and sound conclusion derivation."
    eval_tags = [EvalTags.FUTURE_EVALS, EvalTags.LLMS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class LegalCompliance(EvalTemplate):
    eval_id = "71"
    name = "Legal Compliance"
    description = "Evaluates content for compliance with legal requirements, regulatory standards, and industry-specific regulations. Identifies potential legal risks and compliance violations."
    eval_tags = [EvalTags.FUTURE_EVALS, EvalTags.TEXT, EvalTags.LLMS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}


class LLMFunctionCalling(EvalTemplate):
    eval_id = "72"
    name = "Evaluate LLM Function calling"
    description = "Assesses accuracy and effectiveness of LLM function calls"
    eval_tags = [EvalTags.FUTURE_EVALS, EvalTags.LLMS]
    required_keys = [
        RequiredKeys.input.value,
        RequiredKeys.output.value,
        RequiredKeys.context.value,
    ]
    optional_keys = [RequiredKeys.context.value, RequiredKeys.input.value]
    output = "score"
    eval_type_id = "OutputEvaluator"
    config_schema = {"check_internet": {"type": "boolean", "default": False}}
