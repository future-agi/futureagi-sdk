"""
Template class shells for cloud evals.

These classes exist purely for IDE autocomplete and backward compatibility
with code that does ``from fi.evals import Toxicity``. Input schemas are
no longer hardcoded here — the cloud registry (``fi.evals.core.cloud_registry``)
fetches ``required_keys`` from the api and maps user inputs dynamically.

To call an eval by name without importing a class, just pass the string::

    evaluate("customer_agent_query_handling", conversation=[...], model="turing_flash")

Renamed templates have a module-level alias from the old name to the new
class (e.g. ``NoOpenAIReference = NoLLMReference``) so existing user code
keeps working seamlessly. Templates that were removed outright are gone —
an ``ImportError`` is a clearer signal than a silent runtime 400.
"""
from typing import Any, Dict, List, Optional

from fi.utils.errors import MissingRequiredConfigForEvalTemplate


# ---------------------------------------------------------------------------
# EvalTemplate base class
# ---------------------------------------------------------------------------

class EvalTemplate:
    """Lightweight marker for cloud eval templates.

    Input filtering and validation happen dynamically via the cloud
    registry — no hardcoded Input schema.
    """

    eval_id: str = ""
    eval_name: str = ""
    description: str = ""
    eval_tags: List[str] = []
    required_keys: List[str] = []
    output: str = ""
    eval_type_id: str = ""
    config_schema: Dict[str, Any] = {}
    criteria: str = ""
    choices: List[str] = []
    multi_choice: bool = False

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def __repr__(self) -> str:
        return f"EvalTemplate(name={self.eval_name})"

    def validate_config(self, config: Dict[str, Any]) -> None:
        for key in self.config_schema:
            if key not in config:
                raise MissingRequiredConfigForEvalTemplate(key, self.eval_name)


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

from ._templates_safety import ConversationCoherence
ConversationCoherence.__module__ = __name__


from ._templates_safety import ConversationResolution
ConversationResolution.__module__ = __name__


# ---------------------------------------------------------------------------
# Content moderation & safety
# ---------------------------------------------------------------------------

from ._templates_safety import ContentModeration
ContentModeration.__module__ = __name__


from ._templates_safety import PII
PII.__module__ = __name__


from ._templates_safety import Toxicity
Toxicity.__module__ = __name__


from ._templates_safety import Sexist
Sexist.__module__ = __name__


from ._templates_safety import PromptInjection
PromptInjection.__module__ = __name__


from ._templates_safety import DataPrivacyCompliance
DataPrivacyCompliance.__module__ = __name__


from ._templates_safety import NoRacialBias
NoRacialBias.__module__ = __name__


from ._templates_safety import NoGenderBias
NoGenderBias.__module__ = __name__


from ._templates_safety import NoAgeBias
NoAgeBias.__module__ = __name__


from ._templates_safety import NoLLMReference
NoLLMReference.__module__ = __name__


# Alias: old class name → current eval. Import-level backward compatibility.
NoOpenAIReference = NoLLMReference


from ._templates_safety import NoApologies
NoApologies.__module__ = __name__


from ._templates_safety import ContentSafety
ContentSafety.__module__ = __name__


from ._templates_safety import NoHarmfulTherapeuticGuidance
NoHarmfulTherapeuticGuidance.__module__ = __name__


from ._templates_safety import ClinicallyInappropriateTone
ClinicallyInappropriateTone.__module__ = __name__


from ._templates_safety import IsHarmfulAdvice
IsHarmfulAdvice.__module__ = __name__


# ---------------------------------------------------------------------------
# RAG / Grounding
# ---------------------------------------------------------------------------

from ._templates_quality import ContextAdherence
ContextAdherence.__module__ = __name__


from ._templates_quality import ContextRelevance
ContextRelevance.__module__ = __name__


from ._templates_quality import Completeness
Completeness.__module__ = __name__


from ._templates_quality import ChunkAttribution
ChunkAttribution.__module__ = __name__


from ._templates_quality import ChunkUtilization
ChunkUtilization.__module__ = __name__


from ._templates_quality import Groundedness
Groundedness.__module__ = __name__


from ._templates_quality import FactualAccuracy
FactualAccuracy.__module__ = __name__


from ._templates_quality import DetectHallucination
DetectHallucination.__module__ = __name__


# Alias: old class name → current eval.
DetectHallucinationMissingInfo = DetectHallucination


from ._templates_quality import IsFactuallyConsistent
IsFactuallyConsistent.__module__ = __name__


# ---------------------------------------------------------------------------
# Tone & quality
# ---------------------------------------------------------------------------

from ._templates_quality import Tone
Tone.__module__ = __name__


from ._templates_quality import PromptAdherence
PromptAdherence.__module__ = __name__


from ._templates_quality import IsPolite
IsPolite.__module__ = __name__


from ._templates_quality import IsConcise
IsConcise.__module__ = __name__


from ._templates_quality import IsHelpful
IsHelpful.__module__ = __name__


from ._templates_quality import IsInformalTone
IsInformalTone.__module__ = __name__


from ._templates_quality import AnswerRefusal
AnswerRefusal.__module__ = __name__


from ._templates_quality import TaskCompletion
TaskCompletion.__module__ = __name__


# ---------------------------------------------------------------------------
# Format / structure
# ---------------------------------------------------------------------------

from ._templates_specialized import IsJson
IsJson.__module__ = __name__


from ._templates_specialized import OneLine
OneLine.__module__ = __name__


from ._templates_specialized import ContainsValidLink
ContainsValidLink.__module__ = __name__


from ._templates_specialized import IsEmail
IsEmail.__module__ = __name__


from ._templates_specialized import ContainsCode
ContainsCode.__module__ = __name__


# ---------------------------------------------------------------------------
# Comparison / matching
# ---------------------------------------------------------------------------

from ._templates_specialized import Ranking
Ranking.__module__ = __name__


from ._templates_specialized import SummaryQuality
SummaryQuality.__module__ = __name__


from ._templates_specialized import IsGoodSummary
IsGoodSummary.__module__ = __name__


from ._templates_specialized import FuzzyMatch
FuzzyMatch.__module__ = __name__


from ._templates_specialized import BleuScore
BleuScore.__module__ = __name__


from ._templates_specialized import TranslationAccuracy
TranslationAccuracy.__module__ = __name__


from ._templates_specialized import CulturalSensitivity
CulturalSensitivity.__module__ = __name__


from ._templates_specialized import BiasDetection
BiasDetection.__module__ = __name__


from ._templates_specialized import GroundTruthMatch
GroundTruthMatch.__module__ = __name__


# ---------------------------------------------------------------------------
# Function calling
# ---------------------------------------------------------------------------

from ._templates_specialized import EvaluateFunctionCalling
EvaluateFunctionCalling.__module__ = __name__


# Alias: old class name → current eval.
LLMFunctionCalling = EvaluateFunctionCalling


# ---------------------------------------------------------------------------
# Domain / agent / multimodal
# ---------------------------------------------------------------------------

from ._templates_specialized import TextToSQL
TextToSQL.__module__ = __name__


from ._templates_specialized import PromptInstructionAdherence
PromptInstructionAdherence.__module__ = __name__


from ._templates_specialized import ProtectFlash
ProtectFlash.__module__ = __name__


from ._templates_specialized import ImageInstructionAdherence
ImageInstructionAdherence.__module__ = __name__


from ._templates_specialized import SyntheticImageEvaluator
SyntheticImageEvaluator.__module__ = __name__


from ._templates_specialized import OCREvaluation
OCREvaluation.__module__ = __name__


from ._templates_specialized import ASRAccuracy
ASRAccuracy.__module__ = __name__


# Alias: old class name → current eval.
AudioTranscriptionEvaluator = ASRAccuracy


from ._templates_specialized import TTSAccuracy
TTSAccuracy.__module__ = __name__


from ._templates_specialized import AudioQualityEvaluator
AudioQualityEvaluator.__module__ = __name__


from ._templates_specialized import CaptionHallucination
CaptionHallucination.__module__ = __name__


from ._templates_specialized import IsCompliant
IsCompliant.__module__ = __name__


# ---------------------------------------------------------------------------
# Customer-agent family (new in revamp)
# ---------------------------------------------------------------------------

from ._templates_specialized import CustomerAgentClarificationSeeking
CustomerAgentClarificationSeeking.__module__ = __name__


from ._templates_specialized import CustomerAgentContextRetention
CustomerAgentContextRetention.__module__ = __name__


from ._templates_specialized import CustomerAgentConversationQuality
CustomerAgentConversationQuality.__module__ = __name__


from ._templates_specialized import CustomerAgentHumanEscalation
CustomerAgentHumanEscalation.__module__ = __name__


from ._templates_specialized import CustomerAgentInterruptionHandling
CustomerAgentInterruptionHandling.__module__ = __name__


from ._templates_specialized import CustomerAgentLanguageHandling
CustomerAgentLanguageHandling.__module__ = __name__


from ._templates_specialized import CustomerAgentLoopDetection
CustomerAgentLoopDetection.__module__ = __name__


from ._templates_specialized import CustomerAgentObjectionHandling
CustomerAgentObjectionHandling.__module__ = __name__


from ._templates_specialized import CustomerAgentPromptConformance
CustomerAgentPromptConformance.__module__ = __name__


from ._templates_specialized import CustomerAgentQueryHandling
CustomerAgentQueryHandling.__module__ = __name__


from ._templates_specialized import CustomerAgentTerminationHandling
CustomerAgentTerminationHandling.__module__ = __name__
