"""Optional runtime attribution. Never creates an OTel provider or exporter.

``configure()`` with no arguments restores environment/provider discovery.
Importing this package does not import OpenTelemetry.
"""

__all__ = ["configure", "agent_scope", "declare_skill", "status", "FutureAGISkillsSpanProcessor"]


def __getattr__(name):
    if name == "configure":
        from ._otel import configure
        return configure
    if name == "agent_scope":
        from ._scope import agent_scope
        return agent_scope
    if name == "declare_skill":
        from ._hooks import declare_skill
        return declare_skill
    if name == "status":
        from ._status import status
        return status
    if name == "FutureAGISkillsSpanProcessor":
        from .processor import FutureAGISkillsSpanProcessor
        return FutureAGISkillsSpanProcessor
    raise AttributeError(name)
