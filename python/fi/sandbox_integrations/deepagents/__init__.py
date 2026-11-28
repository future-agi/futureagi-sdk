"""A Deep Agents backend that runs an agent's tools in a Future AGI sandbox (Python 3.11+)::

    pip install "futureagi[sandbox-deepagents]"

    from deepagents import create_deep_agent
    from fi.sandbox import Sandbox
    from fi.sandbox_integrations.deepagents import FutureAGISandbox

    with Sandbox.create(name="agent-scratch") as sbx:
        agent = create_deep_agent(model="...", backend=FutureAGISandbox(sandbox=sbx))

Importing this module on Python 3.10 raises ``ImportError``; without Deep Agents installed it raises
``fi.errors.MissingExtraError``. See ``README.md`` in this folder.
"""

from ._backend import (
    CHECK_TIMEOUT_S,
    DEFAULT_TIMEOUT_S,
    DEFAULT_WORKDIR,
    FILES_ROOT,
    FutureAGISandbox,
)

__all__ = [
    "CHECK_TIMEOUT_S",
    "DEFAULT_TIMEOUT_S",
    "DEFAULT_WORKDIR",
    "FILES_ROOT",
    "FutureAGISandbox",
]
