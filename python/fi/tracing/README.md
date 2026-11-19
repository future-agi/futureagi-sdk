# Observe queries

Use `client.tracing` to read projects, traces, sessions, end users, spans and error
clusters, or to manage dashboards. Python offers async and synchronous clients;
TypeScript uses the same method names in camelCase. Each namespace shares the
root client's credentials, connection pool, retries and typed errors.

Create a personal API key explicitly in your account and set `FI_API_KEY` and
`FI_SECRET_KEY`. Keys are person-owned; this client does not create or fetch an
organization key. Set `FI_BASE_URL` for your deployment.

## Error-feed licensing

Error-feed calls (`issues`, `issue`, and `issue_stats` / `issueStats`) require an
Enterprise licence on self-hosted servers, or an eligible cloud plan. If this
server has no licence, HTTP 402 `LICENSE_MISSING` raises `LicenseRequiredError`,
a subclass of `PaymentRequiredError` and `FutureAGIAPIError`. Ask the server
administrator to configure a licence that includes `error_feed`. Other HTTP 402
denials raise `PaymentRequiredError`; they do not necessarily mean a licence
is missing. This applies to the error-feed calls in both examples below.

## Python

```python
from fi import AsyncFutureAGIClient

async def inspect_trace(project_id: str, trace_id: str):
    async with AsyncFutureAGIClient() as client:
        projects = await client.tracing.projects(page_size=20)
        sessions = await client.tracing.sessions(project_id=project_id)
        users = await client.tracing.users(project_id=project_id)
        page = await client.tracing.spans_by_trace(
            trace_id, project_id=project_id, page_size=30
        )
        issues = await client.tracing.issues(project_id=project_id)
        dashboards = await client.tracing.dashboards.list()
        return page
```

`FutureAGIClient` is the synchronous twin: use `with`, not `async with`, and omit
`await`. Methods return the server's JSON envelope unchanged, including page,
identity, parent-child and query-completeness fields. Dashboards retain their
own declared response shapes; widget lists expose the shared page iterator.

## TypeScript

```typescript
import { FutureAGIClient } from "@future-agi/sdk";

const client = new FutureAGIClient();
const projects = await client.tracing.projects({ page_size: 20 });
const page = await client.tracing.spansByTrace("trace-id", {
  project_id: "project-id", page_size: 30,
});
const issues = await client.tracing.issues({ project_id: "project-id" });
const dashboards = await client.tracing.dashboards.list();
```

Query object keys follow the server's snake_case spelling in both languages.
`spans_by_trace` / `spansByTrace` requires a project as well as a trace ID, because
the same trace ID can exist in several projects. Extra filters are added to the
trace filter, never substituted for it. Supply additional filters as a list of
filter mappings; this helper encodes the list as JSON without modifying it.
Other query methods accept the server's JSON-encoded filter strings.

## Pagination and identity

A span request reads **one bounded page**, not necessarily the entire trace.
Inspect `result.metadata`, including any `has_more`, `next_cursor`, lower-bound
row counts and completeness indicators returned by the server. To continue,
call the same method with the same scope and filters, `cursor_mode=True` and
`cursor=<next_cursor>` (TypeScript uses `true`). Do not mix a cursor with
`page_number`. The client never follows a server-supplied pagination URL.

`get_span` / `getSpan` can take the server's physical-identity selectors, including
project, trace, start hour, observation type, service and expected version.
Pass the complete selector from the read result when identifying a particular
copy; a bare span ID does not identify a unique physical copy in every import.
`get_trace` / `getTrace` returns the trace detail, including any tree supplied by
the server, without flattening parent-child relationships.

Error clusters keep the existing `issues`, `issue`, and `issue_stats` /
`issueStats` names. `error_analysis` / `errorAnalysis` reads a trace's recorded
analysis. Reading analysis does not start an analysis job or call a model.
Online evaluation task management is not offered by this namespace.

## Instrument with traceAI

The platform SDK queries stored traces; it does **not** supply a tracing
decorator, instrument a model provider or export OpenTelemetry spans.
Instrumentation remains in the separate [traceAI project](https://github.com/future-agi/traceAI).

```bash
pip install "futureagi[tracing]"
```

On Python 3.10 through 3.13, this extra installs traceAI's
`fi-instrumentation-otel` package (`fi_instrumentation`). Follow traceAI's
`register()` instructions and install its provider-specific `traceai-*`
instrumentors as needed. For TypeScript, use traceAI's `@traceai/*` packages and
their documented setup; installing `@future-agi/sdk` alone does not instrument
an application. Configure instrumentation for the same deployment and personal
credentials as the query client.
