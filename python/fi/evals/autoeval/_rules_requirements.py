"""Requirements for rules."""
from __future__ import annotations

from fi.evals.autoeval.rules import (AppCategory, AppRequirement, Dict, List)

CATEGORY_REQUIREMENTS: Dict[AppCategory, List[AppRequirement]] = {
    AppCategory.CUSTOMER_SUPPORT: [
        AppRequirement(
            category="quality",
            importance="required",
            reason="Customer support needs clear, coherent responses",
            suggested_evals=["answer_relevancy"],
        ),
        AppRequirement(
            category="safety",
            importance="required",
            reason="Customer interactions must be safe and appropriate",
            suggested_scanners=["jailbreak", "toxicity"],
        ),
        AppRequirement(
            category="pii_protection",
            importance="recommended",
            reason="Customer data should be protected",
            suggested_scanners=["pii", "secrets"],
        ),
    ],
    AppCategory.RAG_SYSTEM: [
        AppRequirement(
            category="faithfulness",
            importance="required",
            reason="RAG systems must provide grounded, faithful responses",
            suggested_evals=["faithfulness", "groundedness"],
        ),
        AppRequirement(
            category="quality",
            importance="required",
            reason="Responses should be coherent and relevant",
            suggested_evals=["answer_relevancy"],
        ),
        AppRequirement(
            category="safety",
            importance="required",
            reason="Prevent prompt injection attacks",
            suggested_scanners=["jailbreak", "prompt_injection"],
        ),
    ],
    AppCategory.CODE_ASSISTANT: [
        AppRequirement(
            category="quality",
            importance="required",
            reason="Code responses should be coherent",
            suggested_evals=["answer_relevancy"],
        ),
        AppRequirement(
            category="code_safety",
            importance="required",
            reason="Prevent malicious code generation",
            suggested_scanners=["code_injection", "secrets", "jailbreak"],
        ),
    ],
    AppCategory.CONTENT_MODERATION: [
        AppRequirement(
            category="safety",
            importance="required",
            reason="Content moderation requires comprehensive safety checks",
            suggested_scanners=["toxicity", "bias", "invisible_chars"],
        ),
    ],
    AppCategory.AGENT_WORKFLOW: [
        AppRequirement(
            category="tool_use",
            importance="required",
            reason="Agent workflows need tool use validation",
            suggested_evals=["action_safety"],
        ),
        AppRequirement(
            category="safety",
            importance="required",
            reason="Agent actions must be safe",
            suggested_evals=["action_safety"],
            suggested_scanners=["jailbreak", "code_injection"],
        ),
        AppRequirement(
            category="reasoning",
            importance="recommended",
            reason="Agent reasoning should be high quality",
            suggested_evals=["reasoning_quality"],
        ),
    ],
}


DEFAULT_REQUIREMENTS: List[AppRequirement] = [
    AppRequirement(
        category="quality",
        importance="recommended",
        reason="All LLM applications benefit from basic quality evaluation",
        suggested_evals=["answer_relevancy"],
    ),
]
