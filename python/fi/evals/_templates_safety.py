"""Safety for templates."""
from __future__ import annotations

from fi.evals.templates import (EvalTemplate)

class ConversationCoherence(EvalTemplate):
    eval_name = "conversation_coherence"
    eval_id = "1"


class ConversationResolution(EvalTemplate):
    eval_name = "conversation_resolution"
    eval_id = "2"


class ContentModeration(EvalTemplate):
    eval_name = "content_moderation"
    eval_id = "4"


class PII(EvalTemplate):
    eval_name = "pii"
    eval_id = "14"


class Toxicity(EvalTemplate):
    eval_name = "toxicity"
    eval_id = "15"


class Sexist(EvalTemplate):
    eval_name = "sexist"
    eval_id = "17"


class PromptInjection(EvalTemplate):
    eval_name = "prompt_injection"
    eval_id = "18"


class DataPrivacyCompliance(EvalTemplate):
    eval_name = "data_privacy_compliance"
    eval_id = "22"


class NoRacialBias(EvalTemplate):
    eval_name = "no_racial_bias"
    eval_id = "77"


class NoGenderBias(EvalTemplate):
    eval_name = "no_gender_bias"
    eval_id = "78"


class NoAgeBias(EvalTemplate):
    eval_name = "no_age_bias"
    eval_id = "79"


class NoLLMReference(EvalTemplate):
    """Checks that the output doesn't reference the underlying LLM (e.g. 'I am GPT…').

    Replaced the old ``NoOpenAIReference`` template in the api revamp.
    """

    eval_name = "no_llm_reference"


class NoApologies(EvalTemplate):
    eval_name = "no_apologies"
    eval_id = "81"


class ContentSafety(EvalTemplate):
    eval_name = "content_safety_violation"
    eval_id = "93"


class NoHarmfulTherapeuticGuidance(EvalTemplate):
    eval_name = "no_harmful_therapeutic_guidance"
    eval_id = "90"


class ClinicallyInappropriateTone(EvalTemplate):
    eval_name = "clinically_inappropriate_tone"
    eval_id = "91"


class IsHarmfulAdvice(EvalTemplate):
    eval_name = "is_harmful_advice"
    eval_id = "92"
