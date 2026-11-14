# OpenAI Agents SDK sandbox client

`fi.sandbox_integrations.openai_agents` lets an OpenAI Agents SDK `SandboxAgent` run its commands and keep its
files in a Future AGI sandbox. You pass `FutureAGISandboxClient` to `SandboxRunConfig(client=...)`; the agent
definition stays the same.

These integrations ship in the Future AGI SDK (`pip install futureagi`).

## Install

```bash
pip install futureagi "openai-agents>=0.24,<0.25"
```

There is no `futureagi` extra for this integration, so install the Agents SDK directly. The supported range is
`openai-agents>=0.24,<0.25`. The client builds on the SDK's sandbox base classes, some of whose hooks are
underscored, so other versions are not supported. Without the SDK's sandbox support installed,
importing the module raises `fi.errors.MissingExtraError` with that install line.

openai-agents 0.24 needs `openai` 3 or later, while `futureagi[evals]` needs `openai` below 3, so this integration
cannot be installed in the same environment as `futureagi[evals]`. Use a separate environment for each; pip reports
the conflict when both are asked for.

## Quickstart

```python
from agents import Runner, RunConfig
from agents.sandbox import SandboxAgent, SandboxRunConfig
from fi.sandbox_integrations.openai_agents import FutureAGISandboxClient, FutureAGISandboxClientOptions

agent = SandboxAgent(name="fixer", instructions="Fix the failing test in the workspace.")

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
```

`FutureAGISandboxClient()` reads the environment, as `fi.sandbox.AsyncSandbox` does: `OMEGA_BASE_URL`, then
`FI_API_KEY` and `FI_SECRET_KEY` (hosted) or `FUTUREAGI_OMEGA_API_KEY` (self-hosted EE), and `FI_WORKSPACE_ID` /
`FI_ORGANIZATION_ID` as the scope. To pass them in code, build the client and hand it over:

```python
from fi import AsyncFutureAGIClient

client = FutureAGISandboxClient(client=AsyncFutureAGIClient(api_key=..., secret_key=..., platform_base_url=...))
```

A missing or conflicting setting raises `fi.sandbox.ConfigurationError` before anything is sent.

## Options

`FutureAGISandboxClientOptions` (every field optional; passing no options at all uses these defaults):

| Option | Default | What it does |
|---|---|---|
| `name` | none | The sandbox's name. |
| `template` | the deployment's | The sandbox template (`base`, `python-data`, `node-web`, ...). |
| `size` | the deployment's | `small`, `medium`, `large` or `xl`. |
| `image` | none | An image the deployment allows, instead of a template. |
| `idle_ttl_seconds` | the deployment's | How long an idle sandbox lives. |
| `workdir` | `/workspace` | The workspace root when the run passes no manifest; `/workspace` or a folder inside it. |
| `exec_timeout_s` | the workspace's maximum | The time limit of a command run without one. |
| `hibernate_on_exit` | `False` | Hibernate the sandbox at the end of a run instead of deleting it. Hibernation keeps the files, not the running processes. |

Every command's time limit is rounded up to whole seconds and kept within the workspace's exec maximum
(`caps.exec.maxTimeoutSeconds` of the workspace's sandbox settings, read when a session is made).

## How a command ends

A command runs once, in the workspace root, with `/bin/sh`. The sandbox exec API takes the working folder
relative to `/workspace` and refuses an absolute one, so the client sends the root that way (`/workspace/proj`
goes as `proj`; `/workspace` itself goes as no folder). Its `ExecResult.exit_code` is the code the
`futureagi sandbox exec` command uses:

| How it ended | `exit_code` | Line added to stderr |
|---|---|---|
| it exited | its own code | none |
| it ran past its time limit | 124 | `Command timed out after N seconds` |
| signal N ended it | 128 + N (Linux numbering) | `Command was ended by signal SIG...` |
| it was cancelled | 130 | `Command was cancelled` |
| it could not start, or ended without a code | 1 | why |

When the connection ends before the command's exit, or the sandbox fails after the command started, the client
raises the SDK's `ExecTransportError` (not retryable). Whether such a command finished is unknown, so it is never
sent again.

## Resume and snapshots

- At the end of a run the sandbox is deleted, or hibernated with `hibernate_on_exit=True`.
- When a run resumes from its saved state, the client reattaches to the same sandbox. A hibernated sandbox is
  resumed once (this is the only place the client resumes a sandbox). A sandbox that is gone is replaced by a new
  one made with the same options, and the SDK fills it from the session's snapshot. A sandbox that needs recovery
  is refused, so it is not left using one of the workspace's sandbox slots.
- `persist_workspace` packs the workspace root into a tar stream with workspace-relative member paths, through a
  temporary `/workspace/.fi-ws-<id>.tar` that is removed afterwards; `hydrate_workspace` does the reverse. A
  stream above 64 MiB (the upload limit of one file) is refused before anything is sent. A failed call can leave
  that temporary file behind; files named `.fi-ws-*.tar` are never put into an archive.

## What is refused

These are refused before any request, with `NotImplementedError` naming what was asked (exposed ports with the
SDK's own `ExposedPortUnavailableError`):

- Running a command or reading or writing a file as another user (`user=`, `run_as=`, manifest users and groups,
  an entry with an owner): sandboxes run every command as one fixed user (uid 1000).
- PTY sessions and exposed ports.
- Manifest entries other than files and folders (`File`, `Dir`, `LocalFile`, `LocalDir`): mounts and git
  repositories are refused.
- Manifest environment variables: the client sends no environment with a command. Command environments carry
  plain, non-secret values only; never put keys there.
- A workspace root outside `/workspace`, because the sandbox files API reaches files under `/workspace` only. A
  read or write of a path outside it is refused the same way.

## The MCP alternative

An agent can also reach a sandbox through MCP tools, with no client code: run the SDK's MCP server and give it
to any `Agent`. Pass the server its settings through `env`: the stdio client does not hand your environment to
the server it starts, and without an address and a credential the server exits (code 2) before serving.

```python
import os

from agents import Agent
from agents.mcp import MCPServerStdio

settings = {name: os.environ[name] for name in ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY")}
async with MCPServerStdio(
    params={"command": "futureagi-py", "args": ["sandbox", "mcp"], "env": settings},
) as server:
    agent = Agent(name="assistant", instructions="...", mcp_servers=[server])
```

That needs `pip install "futureagi[sandbox-mcp]"`. `fi/sandbox_integrations/mcp_server/README.md` lists every
setting the server reads (a self-hosted EE gives `FUTUREAGI_OMEGA_API_KEY` instead of the key pair).

## Hosted limits

Hosted sandboxes have no network access today, so a command inside a hosted sandbox cannot reach the internet.

## Coming from `openai-agents[e2b]`

| `E2BSandboxClientOptions` | `FutureAGISandboxClientOptions` |
|---|---|
| `template` | `template` |
| `timeout` | `idle_ttl_seconds` for the sandbox's lifetime; `exec_timeout_s` for a command's default limit |
| `pause_on_exit` | `hibernate_on_exit` |
| `envs` | not offered (no command environment from the client) |
| `exposed_ports` | not offered |
| `mcp` (the in-sandbox MCP gateway) | not offered; see the MCP alternative above |

The package path, the class names and the backend id `futureagi` are provisional names.
