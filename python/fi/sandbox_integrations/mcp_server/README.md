# Sandbox tools over MCP: `futureagi-py sandbox mcp`

These integrations ship in the Future AGI SDK (`pip install futureagi`). Until that release is published, use the
sandbox HTTP API.

`futureagi-py sandbox mcp` is a Model Context Protocol server on standard input and output. Any MCP client (Claude
Code, the OpenAI Agents SDK, Cursor and others) starts it and gets tools to list, create, run commands in, read,
write, list files in and delete Future AGI sandboxes: isolated Linux computers in your workspace that keep their
files under `/workspace` until deleted. When the client disconnects or stops the server, the server deletes the
sandboxes it created, within the short time clients give a server to stop.

## Install

```bash
pip install "futureagi[sandbox-mcp]"
```

The extra installs the official MCP Python SDK (`mcp` 1.30 or later, or 2.2 and later). Without it the command
prints that install line and exits 3.

## Run it

```bash
export OMEGA_BASE_URL=https://<gateway-host>/omega/api
export FI_API_KEY=... FI_SECRET_KEY=...
futureagi-py sandbox mcp
```

After the SDK's console script is renamed, the command is `futureagi sandbox mcp`. The settings are the ones every
sandbox command reads, from the environment only:

| Variable | Meaning |
|---|---|
| `OMEGA_BASE_URL` (or `--base-url URL`) | Where the sandbox API is. Hosted: `https://<gateway-host>/omega/api`. Self-hosted: your EE's address with its port. There is no default. |
| `FI_API_KEY`, `FI_SECRET_KEY` | Your Future AGI API key pair (hosted). |
| `FUTUREAGI_OMEGA_API_KEY` | An EE account key (self-hosted, loopback addresses only from the command line). Set this or the pair, not both. |
| `FI_WORKSPACE_ID`, `FI_ORGANIZATION_ID` | Optional: the workspace and organization to act in. |

A saved `login` is not read. A missing address or credential is reported on stderr as `code: message` before the
server starts, and the command exits 2.

## Connect a client

Pass the settings through the client's own `env` for the server: do not count on a client handing its own
environment to the server it starts.

**Claude Code.** Options go after the server's name and before `--`; everything after `--` is the command:

```bash
claude mcp add futureagi-sandbox \
  --env OMEGA_BASE_URL=https://<gateway-host>/omega/api --env FI_API_KEY=... --env FI_SECRET_KEY=... \
  -- futureagi-py sandbox mcp
```

`claude mcp add` stores the server in local scope unless you pass `--scope`. `--scope project` writes the entry,
keys included, to the project's `.mcp.json`, which is shared with everyone in the project: keep keys in `local` or
`user` scope.

**Any client with an `mcpServers` file:**

```json
{
  "mcpServers": {
    "futureagi-sandbox": {
      "command": "futureagi-py",
      "args": ["sandbox", "mcp"],
      "env": {
        "OMEGA_BASE_URL": "https://<gateway-host>/omega/api",
        "FI_API_KEY": "...",
        "FI_SECRET_KEY": "..."
      }
    }
  }
}
```

**OpenAI Agents SDK:**

```python
import os

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

settings = {name: os.environ[name] for name in ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY")}
async with MCPServerStdio(
    name="futureagi-sandbox",
    params={"command": "futureagi-py", "args": ["sandbox", "mcp"], "env": settings},
) as server:
    agent = Agent(name="coder", instructions="Use the sandbox to run code.", mcp_servers=[server])
    result = await Runner.run(agent, "Write fizzbuzz.py in a sandbox and run it.")
```

**In code**, without the command line (for example with your own client and transport):

```python
from fi import AsyncFutureAGIClient
from fi.sandbox_integrations.mcp_server import SandboxTools, build_server

client = AsyncFutureAGIClient(api_key=..., secret_key=..., platform_base_url="https://<gateway-host>/omega/api")
tools = SandboxTools(client.sandboxes)
server = build_server(tools)          # an MCPServer (mcp 2.x) or FastMCP (mcp 1.x)
```

Call `await tools.cleanup()` when you stop serving it, to delete the sandboxes it created.

## Tools

| Tool | What it does | Arguments | Result |
|---|---|---|---|
| `sandbox_list` | Lists your sandboxes and the workspace's limits. | none | `{"sandboxes": [{"id", "name", "state", "template", "size", "lastActivityAt"}], "caps": {"maxActiveSandboxes", "templates", "defaultTemplate", "sizes", "defaultSize", "idleTtlSeconds", "exec": {"defaultTimeoutSeconds", "maxTimeoutSeconds", "maxOutputBytes"}}}` |
| `sandbox_create` | Creates a sandbox. | `name` (1 to 120 bytes), `template`, `size`, `idle_ttl_seconds`; all optional | `{"id", "name", "state", "template", "size"}` |
| `sandbox_exec` | Runs a shell command and waits for it to end. | `command`, `sandbox_id`, `cwd`, `timeout_seconds` | `{"exit_code", "signal", "timed_out", "cancelled", "truncated", "duration_ms", "error", "exec_id", "stdout", "stderr", "stdout_clipped", "stderr_clipped"}` |
| `sandbox_read_file` | Reads a file: UTF-8 text as it is, anything else as base64. | `path`, `sandbox_id`, `max_bytes` | `{"path", "encoding", "content", "bytes", "truncated"}` |
| `sandbox_write_file` | Writes a file; missing folders are created. | `path`, `content`, `sandbox_id`, `encoding` (`utf8` or `base64`) | `{"path", "bytes"}` |
| `sandbox_list_files` | Lists a folder (default: the top folder of the sandbox's files). | `path`, `sandbox_id` | `{"path", "entries": [{"name", "size", "directory", "mode"}]}` |
| `sandbox_delete` | Deletes a sandbox and its files for good. A sandbox already gone is not an error. | `sandbox_id` | `{"id", "state"}` |

`sandbox_exec` returns the whole exit record: a non-zero exit, a timeout, a signal and a cancel are results, not
errors. `exit_code` is null after a signal or when the command could not start (`error` says why). `stdout` and
`stderr` each keep their last 20,000 characters (`--max-output-chars N`); when earlier output was dropped, the
`_clipped` flag is true and the text starts with `[... N earlier characters dropped ...]`. `truncated` means the
server itself dropped output beyond its own cap.

A refused or failed call comes back as a tool error whose text is `code: message` and what to do next, for example
`quota_exceeded: ... delete a sandbox you no longer need (sandbox_list shows them) or ask an admin to raise the limit`.
A folder passed to `sandbox_read_file` is refused with a pointer to `sandbox_list_files`; a hibernated sandbox is
refused with the command a person runs to resume it (`futureagi-py sandbox resume SANDBOX_ID`): nothing resumes it
on its own.

## Pinned mode and cleanup on exit

`futureagi-py sandbox mcp --sandbox SANDBOX_ID` serves one sandbox. Only `sandbox_exec`, `sandbox_read_file`,
`sandbox_write_file` and `sandbox_list_files` are offered, `sandbox_id` defaults to that sandbox, and any other id
is refused. Use it to hand an agent one sandbox with no power to create or delete any.

When the client disconnects, or stops the server with SIGTERM or Ctrl-C, the server deletes the sandboxes it
created and prints each one on stderr. A sandbox it did not create is never deleted then. `--keep` keeps them. A
delete that fails is printed as `code: message` and does not stop the others.

Clients give a stopping server only a short grace period: the official MCP SDK closes the server's stdin, waits
2 seconds, then sends SIGTERM. So the deletes are sent together, and a SIGTERM that arrives while they run does
not stop them. If the client kills the server before a delete has finished, that sandbox is kept:
`futureagi-py sandbox list` shows it. The hosted workspace runs at most two active sandboxes, so a forgotten one
blocks the next run: leave `--keep` off unless you need the sandboxes after the session.

If a `sandbox_create` call loses its connection before the answer arrives, whether the sandbox was made is
unknown; the tool error says so and points at `sandbox_list`. A sandbox made that way is not known to the server
and is not deleted on exit.

## Exit codes and time limits

| Exit | When |
|---|---|
| 0 | The client disconnected, or stopped the server with SIGTERM, and the server stopped after the cleanup above. |
| 2 | A setup problem before serving: no address, no credential, both credentials, or an address the command line does not allow (`code: message` on stderr). |
| 3 | The `mcp` package is missing (the message is the install line). |
| 4 | Interrupted (Ctrl-C), after the cleanup above. |

`timeout_seconds` is kept between 1 and the workspace's longest limit (`caps.exec.maxTimeoutSeconds` from
`sandbox_list`, read once per server); left out, the server uses the workspace's default
(`caps.exec.defaultTimeoutSeconds`). A command that runs past its limit ends with `timed_out: true`.

## Security notes

- Credentials come only from the server's environment. No tool takes a key, a credential or an environment
  variable: a command that needs a plain value sets it itself (`export NAME=value; ...`), and a command's
  environment must never hold credentials.
- The server writes nothing but the protocol to stdout and never prints a key; error texts are scrubbed of keys.
- Nothing is sent twice: create, exec, write and delete are never retried. When the client cancels a running
  `sandbox_exec`, the command's stream is closed, which cancels the command.
- Every tool call is a sandbox API call, recorded in the sandbox's audited activity (`sbx.activity()`, or the
  Console).

## Hosted limits

Hosted sandboxes have no network today; full internet access has been decided and is being built. A workspace runs
at most two active sandboxes at a time (`caps.maxActiveSandboxes`).

## Not offered

- File search: run `grep` or `rg` through `sandbox_exec`.
- Port sharing: sandboxes take no inbound connections.
- Usage and metrics.
- Background or streamed commands: `sandbox_exec` waits for the command to end.

The command name `sandbox mcp`, the module path and the extra name `sandbox-mcp` are provisional.
