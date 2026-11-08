"""Specialized for templates."""
from __future__ import annotations

from fi.evals.templates import (EvalTemplate)

class IsJson(EvalTemplate):
    eval_name = "is_json"
    eval_id = "23"


class OneLine(EvalTemplate):
    eval_name = "one_line"
    eval_id = "38"


class ContainsValidLink(EvalTemplate):
    eval_name = "contains_valid_link"
    eval_id = "39"


class IsEmail(EvalTemplate):
    eval_name = "is_email"
    eval_id = "40"


class ContainsCode(EvalTemplate):
    """New in the api revamp."""

    eval_name = "contains_code"


class Ranking(EvalTemplate):
    eval_name = "eval_ranking"
    eval_id = "61"


class SummaryQuality(EvalTemplate):
    eval_name = "summary_quality"
    eval_id = "64"


class IsGoodSummary(EvalTemplate):
    eval_name = "is_good_summary"
    eval_id = "94"


class FuzzyMatch(EvalTemplate):
    eval_name = "fuzzy_match"
    eval_id = "87"


class BleuScore(EvalTemplate):
    eval_name = "bleu_score"
    eval_id = "101"


class TranslationAccuracy(EvalTemplate):
    eval_name = "translation_accuracy"
    eval_id = "67"


class CulturalSensitivity(EvalTemplate):
    eval_name = "cultural_sensitivity"
    eval_id = "68"


class BiasDetection(EvalTemplate):
    eval_name = "bias_detection"
    eval_id = "69"


class GroundTruthMatch(EvalTemplate):
    """New in the api revamp."""

    eval_name = "ground_truth_match"


class EvaluateFunctionCalling(EvalTemplate):
    eval_name = "evaluate_function_calling"
    eval_id = "98"


class TextToSQL(EvalTemplate):
    """New in the api revamp."""

    eval_name = "text_to_sql"


class PromptInstructionAdherence(EvalTemplate):
    """New in the api revamp."""

    eval_name = "prompt_instruction_adherence"


class ProtectFlash(EvalTemplate):
    """New in the api revamp — lightweight prompt-injection check."""

    eval_name = "protect_flash"


class ImageInstructionAdherence(EvalTemplate):
    """New in the api revamp."""

    eval_name = "image_instruction_adherence"


class SyntheticImageEvaluator(EvalTemplate):
    """New in the api revamp."""

    eval_name = "synthetic_image_evaluator"


class OCREvaluation(EvalTemplate):
    """New in the api revamp."""

    eval_name = "ocr_evaluation"


class ASRAccuracy(EvalTemplate):
    """Speech-to-text accuracy eval.

    Replaced the old ``AudioTranscriptionEvaluator`` in the revamp.
    """

    eval_name = "ASR/STT_accuracy"


class TTSAccuracy(EvalTemplate):
    """New in the api revamp."""

    eval_name = "TTS_accuracy"


class AudioQualityEvaluator(EvalTemplate):
    eval_name = "audio_quality"
    eval_id = "75"


class CaptionHallucination(EvalTemplate):
    eval_name = "caption_hallucination"
    eval_id = "100"


class IsCompliant(EvalTemplate):
    eval_name = "is_compliant"
    eval_id = "96"


class CustomerAgentClarificationSeeking(EvalTemplate):
    eval_name = "customer_agent_clarification_seeking"


class CustomerAgentContextRetention(EvalTemplate):
    eval_name = "customer_agent_context_retention"


class CustomerAgentConversationQuality(EvalTemplate):
    eval_name = "customer_agent_conversation_quality"


class CustomerAgentHumanEscalation(EvalTemplate):
    eval_name = "customer_agent_human_escalation"


class CustomerAgentInterruptionHandling(EvalTemplate):
    eval_name = "customer_agent_interruption_handling"


class CustomerAgentLanguageHandling(EvalTemplate):
    eval_name = "customer_agent_language_handling"


class CustomerAgentLoopDetection(EvalTemplate):
    eval_name = "customer_agent_loop_detection"


class CustomerAgentObjectionHandling(EvalTemplate):
    eval_name = "customer_agent_objection_handling"


class CustomerAgentPromptConformance(EvalTemplate):
    eval_name = "customer_agent_prompt_conformance"


class CustomerAgentQueryHandling(EvalTemplate):
    eval_name = "customer_agent_query_handling"


class CustomerAgentTerminationHandling(EvalTemplate):
    eval_name = "customer_agent_termination_handling"
