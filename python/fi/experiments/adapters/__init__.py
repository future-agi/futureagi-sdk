"""Task adapters: a plain callable, LangGraph, LangChain and the OpenAI Agents SDK (this release).

``resolve_task(obj)`` returns a :class:`TaskRunner`. Framework objects are detected by walking
``type(obj).__mro__`` for ``(module prefix, class name)`` pairs, so nothing is imported unless the
object already is one.
"""

from fi.experiments.adapters._base import TaskRunner
from fi.experiments.adapters.detect import resolve_task

__all__ = ["TaskRunner", "resolve_task"]
