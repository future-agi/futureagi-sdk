# Sandbox integrations

These integrations ship in the Future AGI SDK (`pip install futureagi`).

`fi.sandbox_integrations` puts Future AGI sandboxes inside other agent frameworks. Each integration is a subpackage
you import by its own name, with its own install line; `import fi.sandbox_integrations` on its own loads no framework and no
sandbox client. Every integration calls the sandbox handle (`fi.sandbox.Sandbox` / `AsyncSandbox`, or a client's
`sandboxes`), so it gets the handle's settings, errors and limits.

## Integrations

| Integration | Import | Install | Guide |
|---|---|---|---|
| Deep Agents backend (Python 3.11+) | `from fi.sandbox_integrations.deepagents import FutureAGISandbox` | `pip install "futureagi[sandbox-deepagents]"` | [`deepagents/README.md`](deepagents/README.md) |
| MCP server (stdio) | `futureagi-py sandbox mcp`, or `from fi.sandbox_integrations.mcp_server import SandboxTools, build_server` | `pip install "futureagi[sandbox-mcp]"` | [`mcp_server/README.md`](mcp_server/README.md) |
| OpenAI Agents SDK sandbox client | `from fi.sandbox_integrations.openai_agents import FutureAGISandboxClient, FutureAGISandboxClientOptions` | `pip install futureagi "openai-agents>=0.24,<0.25"` (no extra: the Agents SDK is installed directly; not in the same environment as `futureagi[evals]`) | [`openai_agents/README.md`](openai_agents/README.md) |
| Trace context for sandbox commands | `from fi.sandbox_integrations.tracing import tracing_env, run_traced, arun_traced, context_from_env` | none new; it uses the app's own OpenTelemetry when present (for example `futureagi[gateway-otel]`) | [`tracing/README.md`](tracing/README.md) |

The eval runner that fans trials out over sandboxes lives with the experiments engine instead:
`from fi.experiments.sandbox import SandboxEval, run_in_sandboxes` (`pip install "futureagi[experiments]"`), guide in
[`../experiments/sandbox/README.md`](../experiments/sandbox/README.md).

A missing framework raises `fi.errors.MissingExtraError` when you import that integration, and the message names the
install line. `futureagi-py sandbox mcp` without its extra prints the install line and exits 3.

## How a command ended

Every integration turns a command's exit record into one shell-style exit code, the same one `futureagi-py sandbox
exec` exits with. The numbers come from the SDK's one table, `fi.sandbox.types`; the helper the integrations share is
`fi.sandbox_integrations._exit` (`shell_exit_code`, `ending_note`). The first row that applies wins:

| How the command ended | Exit code | Note an integration may add to the output |
|---|---|---|
| It was cancelled | 130 | `Command was cancelled` |
| It ran past its time limit | 124 | `Command timed out after {t} seconds` |
| It could not start | 1 | `The command could not start: {error}` |
| It exited | its own code, 0 included | none |
| Signal N ended it (N is the Linux number) | 128 + N | `Command was ended by signal {signal}` |
| A signal with no known number, or no code at all | left to the integration (the command line exits 1) | `Command ended without an exit code ({signal})` |

Signals are numbered as on Linux, where sandboxes run, whatever your own computer numbers them: `SIGKILL` gives 137
and `SIGTERM` 143. A non-zero exit, a timeout, a signal and a cancel are results, not errors. When the output stream
ends before the exit record arrives, whether the command finished is unknown: no integration runs it again, and each
says so in its framework's own way.

No integration retries a call that changes something (create, run, write, upload, delete), and none resumes a
hibernated sandbox on its own: the error says to resume it first.

## Credentials

- Credentials come only from the environment, as for `Sandbox.create`: `FI_API_KEY` and `FI_SECRET_KEY` (Future AGI cloud)
  or `FUTUREAGI_OMEGA_API_KEY` (self-managed), not both; `FI_WORKSPACE_ID` and `FI_ORGANIZATION_ID` set the scope.
  Or pass a `FutureAGIClient` / `AsyncFutureAGIClient` you built.
- The base URL comes from `OMEGA_BASE_URL`, or from `--base-url` on the `futureagi-py sandbox mcp` command.
- Keys do not come from a tool argument, a command-line argument or a command's `env`. A command's `env` is for plain,
  non-secret values only. The helpers that build `env` refuse `FI_API_KEY`, `FI_SECRET_KEY`,
  `FUTUREAGI_OMEGA_API_KEY`, `FI_PLATFORM_TOKEN` and `OMEGA_OS_API_KEY` with a `ConfigurationError` whose code is
  `secret_in_env`.
- Nothing here logs, prints, records or puts into a trace a key or an `env` value.
- A setup problem (no base URL, both kinds of credential) is a `fi.sandbox.ConfigurationError`. What each
  integration does with it:
  - Deep Agents backend, OpenAI Agents sandbox client and the trace context helpers: raised to your code, not
    turned into a command or tool result.
  - MCP server: `futureagi-py sandbox mcp` checks the address and the credentials before it serves; a problem
    there is printed on stderr as `code: message` and the command exits 2. One that shows up during a tool call
    (for example from `SandboxTools` built in code over a client whose settings are refused on its first call)
    becomes a tool error the model reads: `code: message`, followed by instructions to update the settings and
    restart the server instead of retrying. The console script name `futureagi-py` may change too.
