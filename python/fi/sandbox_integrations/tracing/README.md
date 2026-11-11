# Trace context for sandbox commands

These integrations ship in the Future AGI SDK (`pip install futureagi`).

`fi.sandbox_integrations.tracing` puts a sandbox command into your trace. `run_traced` wraps `sbx.commands.run` in a
client span, `sandbox.exec`, that records how the command ended; `tracing_env` builds the `env` that carries the trace
context into the command; `context_from_env` is the side that reads it back inside the sandbox.

```python
from fi.sandbox_integrations.tracing import tracing_env, run_traced, arun_traced, context_from_env
```

No new extra. It uses your app's own OpenTelemetry (for example through `futureagi[gateway-otel]`, which installs
`opentelemetry-api` and `opentelemetry-sdk`). Without OpenTelemetry, `tracing_env()` adds no trace keys and
`run_traced` runs the command once with your `env`.

## What lands where

| Where | Client span `sandbox.exec` in your trace | Spans made inside the sandbox | Sandbox server spans |
|---|---|---|---|
| Hosted | yes, through your own exporter | not offered: hosted sandboxes have no network access today, and keys may not travel in a command's `env` | no |
| Self-hosted, network on | yes | not offered: Future AGI keys reach code inside a sandbox only through a workspace credential for sandboxes (a separate, audited path), and that path is not documented for SDK use; a command's `env` may never carry `FI_API_KEY` or `FI_SECRET_KEY` (`run_traced` refuses them) | no |

On hosted, only the client span reaches the trace. The `TRACEPARENT` your command receives still names the
`sandbox.exec` span, so anything in the sandbox that can export joins the same trace.

## `tracing_env` with `commands.run`

```python
from opentelemetry import trace

tracer = trace.get_tracer("my-app")
with tracer.start_as_current_span("build"):
    result = sbx.commands.run("python job.py", env={"MODE": "fast", **tracing_env()})
```

By default the result holds `TRACEPARENT` and `TRACESTATE` only (the OpenTelemetry environment-carrier names for W3C
Trace Context), for the span you pass as `span=` or else the current span. `TRACESTATE` is there only when the span
carries trace state. With no valid span, or without OpenTelemetry, there are no trace keys.

Every other key is opt-in and off by default:

| Argument | Adds | From |
|---|---|---|
| `baggage=True` | `BAGGAGE` | the same context |
| `collector=True` | `FI_BASE_URL` (the collector address; not a secret) | `environ` (default `os.environ`) |
| `project_name="..."`, `project_version_name="..."` | `FI_PROJECT_NAME`, `FI_PROJECT_VERSION_NAME` | the arguments only |
| `privacy_flags=True` | every `FI_HIDE_*` and `FI_PII_REDACTION` | `environ` |
| `resource_attributes={...}` | `OTEL_RESOURCE_ATTRIBUTES`: comma-joined `key=value`, values percent-encoded | the argument |

The propagators are the W3C ones, used directly, so the names stay the same whatever `OTEL_PROPAGATORS` says.

## `run_traced`

```python
from fi.sandbox_integrations.tracing import run_traced

result = run_traced(sbx, "pytest -q", cwd="app", env={"CI": "1"}, timeout_seconds=300)
# async: result = await arun_traced(async_sbx, "pytest -q")
```

- Starts a `CLIENT` span named `sandbox.exec` (`span_name=` to change it) from `tracer=`, or from the global
  provider's tracer `fi.sandbox_integrations`, as a child of the current span.
- The command's `env` is your `env` over `tracing_env` for that span: by default `TRACEPARENT` / `TRACESTATE` only.
  Your `env` wins on a clash. The opt-ins of `tracing_env` pass through as keyword arguments; `resource_attributes`
  also gets `sandbox.id=<id>`.
- Calls `sbx.commands.run` once and never again: a command whose stream broke is not re-run.
- Sets `sandbox.id`, `sandbox.exec.id`, `sandbox.exec.exit_code`, `sandbox.exec.signal`, `sandbox.exec.timed_out`,
  `sandbox.exec.cancelled`, `sandbox.exec.truncated`, `sandbox.exec.duration_ms` and `sandbox.exec.shell_exit_code`
  (the one exit-code rule of [`../README.md`](../README.md)); a field the exit record leaves empty is left off.
- A non-zero exit, a timeout, a signal and a cancel are attributes, not an error status. A raised error (for example
  `CommandIncompleteError`, when the stream ends before the exit record) sets the status to ERROR with the error's
  class name and is raised again.
- The command line goes on the span only with `record_command=True`: a command line can carry secrets. An `env` value
  never goes on a span.

These attribute names are provisional: they may change before the first release that includes them.

## Inside the sandbox

traceAI does not read `TRACEPARENT`, so code in the sandbox attaches the context itself before it starts spans, then
always flushes before the process exits (a batch processor drops what it has not sent):

```python
import os
from opentelemetry import context, propagate

token = context.attach(propagate.extract({k.lower(): v for k, v in os.environ.items()
                                          if k in ("TRACEPARENT", "TRACESTATE", "BAGGAGE")}))
# register traceAI or your provider, run the work, then always flush before exit:
provider.force_flush()
```

With `futureagi` installed in the sandbox, `context.attach(context_from_env())` does the same extract. It needs
`opentelemetry-api` where it runs, and returns an empty context when `TRACEPARENT` is missing or malformed.

## Credentials

- A command's `env` is for plain, non-secret values only. `run_traced` refuses `FI_API_KEY`, `FI_SECRET_KEY`,
  `FUTUREAGI_OMEGA_API_KEY`, `FI_PLATFORM_TOKEN` and `OMEGA_OS_API_KEY` in `env` with a `ConfigurationError` whose code
  is `secret_in_env`, before anything is sent; `tracing_env` never returns them (`REFUSED_ENV_NAMES`).
- Future AGI keys reach code inside a sandbox only through a workspace credential for sandboxes (a separate, audited
  path). That path is not documented for SDK use, so exporting from inside the sandbox is not offered.
- Nothing here logs, prints or puts into a span an `env` value or a key.

## Where the trace context travels

The trace context travels only in the command's `env`.

## Names

The package path, the function names and the `sandbox.*` span attribute names are provisional: they may change before
the first release that includes them.
