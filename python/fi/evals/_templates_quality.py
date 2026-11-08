"""Quality for templates."""
from __future__ import annotations

from fi.evals.templates import (EvalTemplate)

class ContextAdherence(EvalTemplate):
    eval_name = "context_adherence"
    eval_id = "5"


class ContextRelevance(EvalTemplate):
    eval_name = "context_relevance"
    eval_id = "9"


class Completeness(EvalTemplate):
    eval_name = "completeness"
    eval_id = "10"


class ChunkAttribution(EvalTemplate):
    eval_name = "chunk_attribution"
    eval_id = "11"


class ChunkUtilization(EvalTemplate):
    eval_name = "chunk_utilization"
    eval_id = "12"


class Groundedness(EvalTemplate):
    eval_name = "groundedness"
    eval_id = "47"


class FactualAccuracy(EvalTemplate):
    eval_name = "factual_accuracy"
    eval_id = "66"


class DetectHallucination(EvalTemplate):
    """Detects hallucinated or unsupported claims in the output.

    Replaced the old ``DetectHallucinationMissingInfo`` template in the revamp.
    """

    eval_name = "detect_hallucination"


class IsFactuallyConsistent(EvalTemplate):
    eval_name = "is_factually_consistent"
    eval_id = "95"


class Tone(EvalTemplate):
    eval_name = "tone"
    eval_id = "16"


class PromptAdherence(EvalTemplate):
    eval_name = "prompt_adherence"
    eval_id = "65"


class IsPolite(EvalTemplate):
    eval_name = "is_polite"
    eval_id = "82"


class IsConcise(EvalTemplate):
    eval_name = "is_concise"
    eval_id = "83"


class IsHelpful(EvalTemplate):
    eval_name = "is_helpful"
    eval_id = "84"


class IsInformalTone(EvalTemplate):
    eval_name = "is_informal_tone"
    eval_id = "97"


class AnswerRefusal(EvalTemplate):
    eval_name = "answer_refusal"
    eval_id = "88"


class TaskCompletion(EvalTemplate):
    eval_name = "task_completion"
    eval_id = "99"
