"""An OpenAI Agents SDK sandbox client that runs a ``SandboxAgent``'s commands and files in a Future AGI
sandbox (openai-agents 0.24)::

    pip install futureagi "openai-agents>=0.24,<0.25"

    from agents import Runner, RunConfig
    from agents.sandbox import SandboxAgent, SandboxRunConfig
    from fi.sandbox_integrations.openai_agents import (
        FutureAGISandboxClient,
        FutureAGISandboxClientOptions,
    )

    result = await Runner.run(
        agent,
        "fix the failing test",
        run_config=RunConfig(
            sandbox=SandboxRunConfig(
                client=FutureAGISandboxClient(),
                options=FutureAGISandboxClientOptions(template="python-data"),
            )
        ),
    )

Without the Agents SDK's sandbox support installed, importing this module raises
``fi.errors.MissingExtraError``. See ``README.md`` in this folder.
"""

from ._client import FutureAGISandboxClient
from ._options import FutureAGISandboxClientOptions, FutureAGISandboxSessionState
from ._session import FutureAGISandboxSession

__all__ = [
    "FutureAGISandboxClient",
    "FutureAGISandboxClientOptions",
    "FutureAGISandboxSession",
    "FutureAGISandboxSessionState",
]
