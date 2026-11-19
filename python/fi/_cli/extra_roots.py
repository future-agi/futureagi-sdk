"""Optional import roots with one unambiguous extra, without importing any extras.

Derived from pyproject's optional dependencies and extra memberships; the table
contract test recomputes it. Base dependencies and shared roots are excluded.
OpenAI and OpenTelemetry are shared through instrumentors even though their
*direct* dependency declarations currently belong only to evals.
"""

from __future__ import annotations

import sys
from typing import Optional

EXTRA_ROOTS = {
    "filelock": "evals",
    "jinja2": "evals",
    "litellm": "evals",
    "nltk": "evals",
    "rouge_score": "evals",
    "tiktoken": "gateway-tokens",
    "traceai_openai": "openai",
    "traceai_openai_agents": "openai-agents",
    "yaml": "evals",
}


def extra_for_module(module: Optional[str]) -> Optional[str]:
    return EXTRA_ROOTS.get(module.split(".", 1)[0]) if module else None


def _loaded_evals_requirement() -> Optional[str]:
    # The Python-version guard has already loaded this module before it raises.
    # Do not import a command group or optional package just to format an error.
    requirement = getattr(sys.modules.get("fi.evals._extras"), "EVALS_REQUIREMENT", None)
    return requirement if isinstance(requirement, str) and requirement else None


def is_evals_requirement(exc: ImportError) -> bool:
    """Recognise only the loaded guard's exact message, not arbitrary ImportErrors."""
    return str(exc) == _loaded_evals_requirement()


def evals_requirement() -> str:
    return (_loaded_evals_requirement()
            or 'Local evaluations require Python 3.11+ and pip install "futureagi[evals]"')
