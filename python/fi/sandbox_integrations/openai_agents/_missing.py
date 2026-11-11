"""The error raised when the Agents SDK's sandbox support is not installed, and the line that installs it.

There is no ``futureagi`` extra for this integration yet: the Agents SDK is installed directly, at the
range this client is written for.
"""

from __future__ import annotations

from fi.errors import MissingExtraError

#: The install line for this integration: the Future AGI SDK and the supported Agents SDK range.
INSTALL_LINE = 'pip install futureagi "openai-agents>=0.24,<0.25"'


def missing_agents_sandbox(cause: Exception) -> MissingExtraError:
    """``MissingExtraError`` naming ``agents.sandbox``, with :data:`INSTALL_LINE` as its install hint."""
    error = MissingExtraError(
        f"agents.sandbox is not installed (it ships in openai-agents 0.24). Run: {INSTALL_LINE}",
        cause,
        module="agents.sandbox",
    )
    error.install_hint = INSTALL_LINE
    return error
