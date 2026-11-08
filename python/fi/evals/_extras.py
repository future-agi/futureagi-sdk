"""Dependency guidance for optional local evaluations, without importing the extra."""

import sys


EVALS_REQUIREMENT = (
    "Local metrics and LLM judges require Python 3.11+ and futureagi[evals]. "
    'Install with: pip install "futureagi[evals]" on Python 3.11+.'
)


# The oldest Python that [evals] supports; the base SDK still allows 3.10.
EVALS_PYTHON = (3, 11)


def require_evals_python() -> None:
    """Reject unsupported local evaluation runtimes before optional imports."""
    if sys.version_info < EVALS_PYTHON:
        raise ImportError(EVALS_REQUIREMENT)


# Exclusive Python upper bounds of [evals] dependencies that do not yet support
# newer interpreters; they match the python markers in pyproject.toml.
PYTHON_LIMITS = {"litellm": (3, 15)}


def dependency_requirement(name: str) -> str:
    """Install guidance for one [evals] dependency on this interpreter."""
    limit = PYTHON_LIMITS.get(name)
    if limit is not None and tuple(sys.version_info[:2]) >= limit:
        newest = "%d.%d" % (limit[0], limit[1] - 1)
        return (
            f"{name} does not support Python {limit[0]}.{limit[1]} or newer, so "
            f"futureagi[evals] features that use it need Python 3.11 to {newest}."
        )
    return EVALS_REQUIREMENT


def import_litellm():
    """Import LiteLLM, failing with a typed error that names it and its limit.

    Every LiteLLM import in the SDK goes through here, including lazy paths
    that never call require_evals_python. A missing LiteLLM is reported as:
    - below the [evals] Python floor, the guard's exact requirement, which the
      CLI classifies as a Python-version problem;
    - where [evals] and LiteLLM support the interpreter, the original error,
      unchanged: it is a missing extra, not a Python-version problem;
    - on Python versions LiteLLM does not support, the standard message plus
      the version limit.
    A missing transitive dependency of LiteLLM is always re-raised unchanged.
    """
    try:
        import litellm
    except ModuleNotFoundError as exc:
        if exc.name != "litellm":
            raise
        version = tuple(sys.version_info[:2])
        if version < EVALS_PYTHON:
            raise ModuleNotFoundError(EVALS_REQUIREMENT, name="litellm") from None
        if version < PYTHON_LIMITS["litellm"]:
            raise
        requirement = dependency_requirement("litellm")
        raise ModuleNotFoundError(
            f"No module named 'litellm'. {requirement}", name="litellm"
        ) from None
    return litellm
