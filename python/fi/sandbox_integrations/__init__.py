"""Future AGI sandboxes inside other agent frameworks.

Each integration is a subpackage that you import by its own name; importing this package loads none
of them, no framework and no sandbox client. Each one needs its extra installed:

``fi.sandbox_integrations.deepagents``
    A Deep Agents backend (Python 3.11+)::

        pip install "futureagi[sandbox-deepagents]"
        from fi.sandbox_integrations.deepagents import FutureAGISandbox

``fi.sandbox_integrations.mcp_server``
    An MCP server with sandbox tools, run as ``futureagi-py sandbox mcp`` or built in code::

        pip install "futureagi[sandbox-mcp]"
        from fi.sandbox_integrations.mcp_server import SandboxTools, build_server

``fi.sandbox_integrations.openai_agents``
    A sandbox client for the OpenAI Agents SDK::

        pip install "futureagi[sandbox-openai-agents]"
        from fi.sandbox_integrations.openai_agents import FutureAGISandboxClient, FutureAGISandboxClientOptions

``fi.sandbox_integrations.tracing``
    Trace context for sandbox commands (no new extra; it uses OpenTelemetry when the app has it)::

        from fi.sandbox_integrations.tracing import tracing_env, run_traced, arun_traced, context_from_env

Every integration reports how a command ended with the exit code the ``sandbox`` command uses
(:mod:`fi.sandbox_integrations._exit`). Credentials come from the environment, as for
``fi.sandbox.Sandbox``, or from a client you build; never from a tool argument or a command's ``env``.
The package path, the extras and the ``sandbox mcp`` command are provisional names. See ``README.md``
in this folder.
"""
