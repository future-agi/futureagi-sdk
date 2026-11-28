<div align="center">

![Future AGI Logo](https://fi-content.s3.ap-south-1.amazonaws.com/Logo.png)

# Future AGI SDK

**The world's most accurate AI evaluation, observability and optimization platform**

[![PyPI version](https://badge.fury.io/py/futureagi.svg)](https://pypi.org/project/futureagi/)
[![Python Support](https://img.shields.io/pypi/pyversions/futureagi.svg)](https://pypi.org/project/futureagi/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[Documentation](https://docs.futureagi.com) | [Website](https://www.futureagi.com) | [Community](https://www.linkedin.com/company/futureagi)

</div>

---

## 🚀 What is Future AGI?

Future AGI empowers GenAI teams to build near-perfect AI applications through comprehensive evaluation, monitoring, and optimization. Our platform provides everything you need to develop, test, and deploy production-ready AI systems with confidence.

### ✨ Key Features

- **🎯 World-Class Evaluations** — Industry-leading evaluation frameworks powered by our Critique AI agent
- **⚡ Ultra-Fast Guardrails** — Real-time safety checks with sub-100ms latency
- **📊 Dataset Management** — Programmatically create, update, and manage AI training datasets
- **🎨 Prompt Workbench** — Version control, A/B testing, and deployment management for prompts
- **📚 Knowledge Base** — Intelligent document management and retrieval for RAG applications
- **📈 Advanced Analytics** — Deep insights into model performance and behavior
- **Simulation** — Use the platform `Client.simulation` resource.
- **Add Observability** — Add observability to your AI system to monitor its performance and behavior


---

## 📦 Installation

### Python
```bash
pip install futureagi
```

The base installation does not install rouge-score.

#### Optional local evaluations

Local metrics and LLM judges require Python 3.11+ and the `[evals]` extra:

```bash
pip install "futureagi[evals]"
```

futureagi[evals] installs rouge-score, which is built from source at install time.
The base SDK and cloud evaluation client continue to support Python 3.10+ without this extra.

### TypeScript/JavaScript
```bash
npm install @future-agi/sdk
# or
pnpm add @future-agi/sdk
```

**Requirements:** Python >= 3.10 | Node.js >= 18

Upgrade to `futureagi` 0.8.1 or later (`@future-agi/sdk` 0.3.1 or later); HTTP to a non-loopback host requires `FI_ALLOW_INSECURE_HTTP=1`.

**Gateway clients:** use `fi.gateway.Gateway` / `AsyncGateway` for the released compatibility wrappers, or `AgentCC` / `AsyncAgentCC` for explicit-origin clients. These are distinct APIs; see the Gateway section below.

---

## 🔑 Authentication

Get your API credentials from the [Future AGI Dashboard](https://app.futureagi.com):

```bash
export FI_API_KEY="your_api_key"
export FI_SECRET_KEY="your_secret_key"
```

Or set them programmatically:

```python
import os
os.environ["FI_API_KEY"] = "your_api_key"
os.environ["FI_SECRET_KEY"] = "your_secret_key"
os.environ["FI_BASE_URL"] = "https://api.futureagi.com"
```

### Platform client families

The SDK offers two distinct client families:

- `from fi import Client, AsyncClient` selects the released classes, identical to
  `fi.platform.Client` / `fi.platform.AsyncClient`. Their platform resources include
  `client.gateway` for gateway management and `client.simulation` for simulation.
- `from fi import FutureAGIClient, AsyncFutureAGIClient` selects the OpenAPI-backed facade clients
  described below. Their methods, response envelopes and errors are distinct from
  the released platform clients; choose the family your integration targets.

For `fi.platform.Client` and `fi.platform.AsyncClient`, `allow_insecure_http=True`
opts in to direct plain HTTP for eligible non-loopback hosts outside the Future AGI
zone. `False` disables that opt-in even if `FI_ALLOW_INSECURE_HTTP=1`; `None` (the
default) defers to the environment. The option does not permit plain HTTP to a
Future AGI host or plain HTTP via a proxy.

### OpenAPI-backed facade client

For generated API surfaces, use the wrapper client. It handles Future AGI
headers and keeps the generated code replaceable:

```python
from fi import FutureAGIClient

client = FutureAGIClient(api_key="...", secret_key="...")
queues = client.annotation_queues.list(limit=20)
next_item = client.annotation_queues.items.next("queue-id")

datasets = client.datasets.list(page=1)
experiment_rows = client.experiments.rows("experiment-id")
trace_projects = client.tracing.projects()
me = client.users.current()
alert_options = client.alerts.metric_options(project_id="project-id")
```

The low-level OpenAPI clients are regenerated with `scripts/generate-oss-sdk.sh`.
Public method names are controlled by `openapi/sdk/operation-aliases.json` and
`openapi/sdk/wrapper-map.json`.

### Observe queries and instrumentation

`client.tracing` provides projects, sessions, users, trace-scoped span queries,
error clusters and dashboards, with an async Python twin. See the
[Observe guide](fi/tracing/README.md) for bounded pagination and identity selectors.
Use the separate [traceAI](https://github.com/future-agi/traceAI) packages for
instrumentation; `pip install "futureagi[tracing]"` installs its OpenTelemetry
integration. The SDK does not provide its own tracing decorator.

On Python 3.10–3.13, install `futureagi[tracing-grpc]` to use
`fi.evals.otel.ExporterType.OTLP_GRPC`. The `evals` extra also includes the gRPC
exporter on Python 3.11 and later.

---

## 🎯 Quick Start

### 📊 Dataset Management

Create and manage datasets with built-in evaluations:

```python
from fi.datasets import Dataset
from fi.datasets.types import (
    Cell, Column, DatasetConfig, DataTypeChoices,
    ModelTypes, Row, SourceChoices
)

# Create a new dataset
config = DatasetConfig(name="qa_dataset", model_type=ModelTypes.GENERATIVE_LLM)
dataset = Dataset(dataset_config=config)
dataset = dataset.create()

# Define columns
columns = [
    Column(name="user_query", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS),
    Column(name="ai_response", data_type=DataTypeChoices.TEXT, source=SourceChoices.OTHERS),
    Column(name="quality_score", data_type=DataTypeChoices.INTEGER, source=SourceChoices.OTHERS),
]

# Add data
rows = [
    Row(order=1, cells=[
        Cell(column_name="user_query", value="What is machine learning?"),
        Cell(column_name="ai_response", value="Machine learning is a subset of AI..."),
        Cell(column_name="quality_score", value=9),
    ]),
    Row(order=2, cells=[
        Cell(column_name="user_query", value="Explain quantum computing"),
        Cell(column_name="ai_response", value="Quantum computing uses quantum bits..."),
        Cell(column_name="quality_score", value=8),
    ]),
]

# Push data and run evaluations
dataset = dataset.add_columns(columns=columns)
dataset = dataset.add_rows(rows=rows)

# Add automated evaluation
dataset.add_evaluation(
    name="factual_accuracy",
    eval_template="is_factually_consistent",
    required_keys_to_column_names={
        "input": "user_query",
        "output": "ai_response",
        "context": "user_query",
    },
    run=True
)

print("✓ Dataset created with automated evaluations")
```

### 🎨 Prompt Workbench

Version control and A/B test your prompts:

```python
from fi.prompt import Prompt, PromptTemplate, ModelConfig, MessageBase

# Create a versioned prompt template
template = PromptTemplate(
    name="customer_support",
    messages=[
        {"role": "system", "content": "You are a helpful customer support agent."},
        {"role": "user", "content": "Help {{customer_name}} with {{issue_type}}."},
    ],
    variable_names={"customer_name": ["Alice"], "issue_type": ["billing"]},
    model_configuration=ModelConfig(model_name="gpt-4o-mini", temperature=0.7)
)

# Create and version the template
client = Prompt(template)
await client.open()  # Draft v1
await client.commitCurrentVersion("Initial version", set_as_default=True)

# Assign deployment labels
await client.labels().assign("Production", "v1")

# Compile with variables
compiled = client.compile({"customer_name": "Bob", "issue_type": "refund"})
print(compiled)
```

**A/B Testing Example:**

```python
import OpenAI from "openai"
from fi.prompt import Prompt

# Fetch different variants
variant_a = await Prompt.getTemplateByName("customer_support", label="variant-a")
variant_b = await Prompt.getTemplateByName("customer_support", label="variant-b")

# Randomly select and use
import random
selected = random.choice([variant_a, variant_b])
client = Prompt(selected)
compiled = client.compile({"customer_name": "Alice", "issue_type": "refund"})

# Send to your LLM provider
openai = OpenAI(api_key="your_key")
response = openai.chat.completions.create(model="gpt-4o", messages=compiled)
```

The prompt template and label class methods accept the keyword-only
`allow_insecure_http` option. `None` (the default) uses `FI_ALLOW_INSECURE_HTTP`;
`False` overrides that setting. `True` permits direct HTTP to a custom origin,
but does not permit HTTP to Future AGI hosts or through a proxy. Prefer HTTPS.

```python
from fi.prompt import Prompt

templates = Prompt.list_templates(allow_insecure_http=False)
```

### 📚 Knowledge Base (RAG)

Manage documents for retrieval-augmented generation:

```python
from fi.kb import KnowledgeBase

# Initialize client
kb_client = KnowledgeBase(
    fi_api_key="your_api_key",
    fi_secret_key="your_secret_key"
)

# Create a knowledge base with documents
kb = kb_client.create_kb(
    name="product_docs",
    file_paths=["manual.pdf", "faq.txt", "guide.md"]
)

print(f"✓ Knowledge base created: {kb.kb.name}")
print(f"  Files uploaded: {len(kb.kb.file_names)}")

# Update with more files
updated_kb = kb_client.update_kb(
    kb_id=kb.kb.id,
    file_paths=["updates.pdf"]
)

# Delete specific files
kb_client.delete_files_from_kb(file_ids=["file_id_here"])

# Clean up
kb_client.delete_kb(kb_ids=[kb.kb.id])
```

### 🛰️ Gateway (Agent Command Center)

Call models through the Future AGI gateway with the released OpenAI-compatible `Gateway` / `AsyncGateway` wrappers. The explicit-origin `AgentCC` / `AsyncAgentCC` clients are also available in `fi.gateway`:

```python
from fi.gateway import Gateway

gw = Gateway(session_id="checkout-flow")   # FI_GATEWAY_API_KEY; defaults to the Future AGI HTTPS gateway
reply = gw.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(reply.choices[0].message.content)
```

- `AsyncGateway` is the async version (`async with AsyncGateway() as gw: ...`).
- Routing, fallbacks, caching and guardrails: pass `config=fi.gateway.GatewayConfig(...)`.
- The gateway uses its own virtual keys (`sk-agentcc-*`), not `FI_API_KEY`/`FI_SECRET_KEY`. A URL may end in `/v1` or not.
- Only the released `Gateway` / `AsyncGateway` wrappers fall back to the Future AGI HTTPS gateway. `AgentCC` / `AsyncAgentCC` require an origin supplied via `base_url` or a gateway environment variable. Both families enforce the same HTTP-security validation.
- Deprecated compatibility adapters provide the released 0.x gateway APIs and options; warnings identify deprecated usage. Do not assume every standalone `agentcc` call is a drop-in match for the explicit-origin clients.
- Gateway clients accept `allow_insecure_http=True` for direct HTTP to a non-loopback gateway outside the Future AGI domain. `False` opts out for that client, and `None` follows `FI_ALLOW_INSECURE_HTTP=1`. Copies made with `with_options()` retain the setting. The option does not permit proxies to carry plain HTTP requests.
- Optional gateway dependencies: `pip install "futureagi[gateway-tokens]"` for token helpers, or `pip install "futureagi[gateway-otel]"` for OpenTelemetry.
- Managing gateways (keys, providers, request logs, analytics) is a platform API: `fi.Client().gateway`.


---

## 🎯 Core Use Cases

| Feature | Use Case | Benefit |
|---------|----------|---------|
| **Datasets** | Store and version training/test data | Reproducible experiments, automated evaluations |
| **Prompt Workbench** | Version control for prompts | A/B testing, deployment management, rollback |
| **Knowledge Base** | RAG document management | Intelligent retrieval, document versioning |
| **Evaluations** | Automated quality checks | No human-in-the-loop, 100% configurable |
| **Guardrails** | Real-time safety filters | Sub-100ms latency, production-ready |

---

## 📚 Documentation

- **[Complete Documentation](https://docs.futureagi.com)**
- **[Dataset SDK Guide](https://docs.futureagi.com/future-agi/get-started/dataset/adding-dataset/using-sdk)**
- **[Prompt Workbench Guide](https://docs.futureagi.com/products/prompt/how-to/prompt-workbench-using-sdk)**
- **[Knowledge Base Guide](https://docs.futureagi.com/future-agi/get-started/knowledge-base/how-to/create-kb-using-sdk)**
- **[API Reference](https://docs.futureagi.com)**

---

## 🤝 Language Support

| Language | Package | Status |
|----------|---------|--------|
| **Python** | `futureagi` | ✅ Full Support |
| **TypeScript/JavaScript** | `@future-agi/sdk` | ✅ Full Support |
| **Go** | `github.com/future-agi/futureagi-sdk/go/futureagi` | Generated low-level client |
| **Java** | `com.futureagi:futureagi-sdk` | Generated low-level client |
| **REST API** | cURL/HTTP | ✅ Available |

---

## 🆘 Support & Community

- **📧 Email:** support@futureagi.com
- **💼 LinkedIn:** [Future AGI Company](https://www.linkedin.com/company/futureagi)
- **🐦 X (Twitter):** [@FutureAGI_](https://x.com/FutureAGI_)
- **📰 Substack:** [Future AGI Blog](https://substack.com/@futureagi)

---

## 💡 Why Future AGI?

### 🤖 Human-Free Evaluations
Our Critique AI agent delivers powerful evaluations without human-in-the-loop. It's 100% configurable for any use case — if you can imagine it, you can evaluate it.

### 🔒 Privacy First
Don't want to share data? Install our SDK in your private cloud and get all the benefits while keeping your data secure.

### 🎨 Multimodal Support
Work with text, images, audio, video, or any data type. Our platform is truly data-agnostic.

### ⚡ 2-Minute Integration
A few lines of code start your data flowing. No complex setup, no lengthy onboarding.

---

## 📄 License

The Python SDK is licensed under the [Apache License, Version 2.0](LICENSE).

---

<div align="center">

**[Get Started](https://app.futureagi.com) | [View Documentation](https://docs.futureagi.com)**

Made with ❤️ by the Future AGI Team

</div>

### Run your agent over a dataset: `fi.experiments` and `futureagi-py run` (draft)

`fi.experiments` runs your own task over a dataset, scores it, and stores the run. Before it journals or uploads
anything it hides values with the form of credentials: [`fi/experiments/README.md`](fi/experiments/README.md) lists
exactly what is redacted. `judge()` defaults to the judge model `gpt-4.1-mini`; an uploaded run needs a dataset
name for its rows (`experiments.dataset("rows.jsonl", name="support-cases")`, CLI `--dataset-name`).

### Dataset versions and external experiment runs (draft)

The typed `FutureAGIClient` facade supports immutable snapshots and caller-executed agent results against the dataset/experiment API stack. It does not execute your task or evaluator. These methods require the backend changes in core PRs #3473–#3475; this SDK branch is not a published release.

```python
from fi import FutureAGIClient
from fi.generated.openapi_client.models.dataset_version_create import DatasetVersionCreate
from fi.generated.openapi_client.models.external_run_create_request import ExternalRunCreateRequest

with FutureAGIClient(api_key=api_key, secret_key=secret_key, base_url=base_url) as client:
    snapshot = client.datasets.versions.create(dataset_id, DatasetVersionCreate.from_dict({
        "items": [{"input": {"question": "2+2?"}, "expected": "4"}]
    }))
    version = snapshot.result
    cases = client.datasets.versions.get(dataset_id, version.id)
    run = client.experiment_runs.create(ExternalRunCreateRequest.from_dict({
        "run_id": run_id,  # caller-generated UUID, retained for an explicit replay
        "dataset_version_id": str(version.id),
        "expected_items": [{"example_id": str(item.example_id), "trial_number": 1}
                           for item in cases.result.items],
        "evaluator_metric_ids": [metric_id],
    }))
```

`datasets.versions.list(dataset_id, limit=100, offset=0)` and `.get(...)` return one bounded page. `experiment_runs.ingest_results(run_id, ExternalRunResultsRequest)` uploads a bounded batch; `.compare(RunComparisonRequest)` returns generated typed results. Construct requests with the generated models and use `.to_dict()` when a plain JSON-compatible dictionary is needed.

Every facade call makes one HTTP attempt. Snapshot creation has no retry key: a retry after an ambiguous timeout can create another version. To replay run creation or result ingestion, reuse the run UUID or receipt keys and send the same payload. Conflicts, read failures, and comparison failures are returned without automatic retries.

See `examples/dataset_experiment_lifecycle.py` for the complete deterministic snapshot → two caller-owned tasks → local scores → result uploads → comparison workflow, including idempotent replay checks. It is a data-path example, not model-quality or live Observe qualification.

For per-example trial counts, observed score spread, and paired deltas, opt in on
the existing comparison call (requires core PR #3483):

```python
from fi.generated.openapi_client.models.run_comparison_request import RunComparisonRequest

report = client.experiment_runs.compare(RunComparisonRequest.from_dict({
    "baseline_run_id": baseline_run_id,
    "candidate_run_id": candidate_run_id,
    "metric_id": metric_id,
    "include_trial_stability": True,
}))
for example in report.result.trial_stability or []:
    print(example.example_id, example.candidate.score_stddev)
```

The optional `trial_stability` result is `UNSET` when the backend omits it. Nullable
statistics are `None`; a standard deviation of `None` means fewer than two
assessed values, while `0.0` means observed zero spread. This is descriptive
analysis, not statistical significance. It can be requested with `release_gate`
without changing the gate's verdict.

## Webhooks

Future AGI sends signed HTTP requests to your endpoints when, for example, a prompt label moves or a deployment run
ends. `fi.webhooks` verifies them and manages endpoints; `futureagi-py webhooks` does the same from a shell.

### Verify a request (receivers)

```python
import os
from fi.webhooks import verify, WebhookVerificationError

def hook(request):                       # Django; Flask: request.get_data(); FastAPI: await request.body()
    try:
        event = verify(body=request.body, headers=request.headers, secret=os.environ["FI_WEBHOOK_SECRET"])
    except WebhookVerificationError as err:  # err.reason: missing_headers, timestamp_too_old, no_matching_signature, ...
        return HttpResponse(status=400)
    if event.get("test"):
        return HttpResponse(status=200)
    ...                                   # handle event["type"]; dedupe on event["id"] (at-least-once delivery)
    return HttpResponse(status=200)
```

- Verify the **raw** body: a body that was parsed and serialized again does not verify.
- Requests use [Standard Webhooks](https://www.standardwebhooks.com/) v1 (`webhook-id`, `webhook-timestamp`,
  `webhook-signature`), so any Standard Webhooks library verifies them too. During a secret rotation two `v1,` entries
  are sent and either secret verifies. Timestamps more than 300 s away from the current time are refused (`tolerance_s=`).
- `fi.webhooks.verify` imports only the standard library and ships in `futureagi`.
  There is no separate webhook distribution; any Standard Webhooks library can also verify requests.
- A malformed secret raises `WebhookSecretError`, not `WebhookVerificationError`: let it surface as a 5xx, so the
  sender retries the delivery. Correct the secret so a retry can succeed.

### Manage endpoints from code

```python
from fi.webhooks import Webhooks

with Webhooks() as wh:                    # FI_API_KEY / FI_SECRET_KEY, or `futureagi-py login`
    ep = wh.endpoints.create(
        url="https://hooks.acme.ai/fi",
        events=["prompt.label.changed"],
        filters={"prompt.label.changed": {"label_names": ["Production"], "actions": ["moved", "assigned"]}},
    )
    store_secret(ep.secret)               # returned once; a lost secret means rotate_secret()
    result = wh.endpoints.test(ep.id, event_type="prompt.label.changed")   # sent by the delivery worker
    print(result.status_code, result.outcome)
    failed = wh.deliveries.list(endpoint=ep.id, status="failed", since="24h")
    wh.deliveries.redeliver_many(endpoint=ep.id, status="failed", since="24h")
    rotation = wh.endpoints.rotate_secret(ep.id, overlap="24h")            # the old secret works for 24 h more
```

`AsyncWebhooks` has the same methods, awaited. Results are dicts of the API's JSON with attribute access
(`ep["status"]` or `ep.status`). Refusals raise `fi.errors` classes (`NotFoundError`, `PermissionDeniedError`, ...)
with the API's `code` (`WEBHOOK_URL_UNSAFE_ADDRESS`, ...) and `attr` (the field).

### `futureagi-py webhooks`

```bash
futureagi-py webhooks create --url https://hooks.acme.ai/fi --event prompt.label.changed --label Production \
  --header-env Authorization=HOOK_AUTH --secret-out ./hook-secret        # file mode 0600; prints only the tail
futureagi-py webhooks list
futureagi-py webhooks test whep_...                    # exits 1 unless the receiver answers 2xx
futureagi-py webhooks deliveries whep_... --status failed --since 24h
futureagi-py webhooks redeliver --endpoint whep_... --status failed --since 24h
futureagi-py webhooks rotate-secret whep_... --overlap 24h --secret-out ./hook-secret
futureagi-py webhooks verify --secret-file ./hook-secret --headers-file req.headers --body-file req.body
```

- The signing secret is printed only to a terminal. When stdout is not a terminal (CI), `create` and
  `rotate-secret` refuse before sending anything unless you pass `--secret-out FILE` or `--show-secret`.
- `--secret-out FILE` is written mode 0600, and FILE is replaced only once the new secret has arrived: a refused,
  failed or interrupted `rotate-secret` leaves the secret your receiver reads where it was.
- `--header 'K: V'` lands in shell history; `--header-file FILE` and `--header-env NAME=ENVVAR` keep values out of it.
  Values are sent literally (no `${...}` expansion). A malformed header line is refused by its line number and is not
  printed.
- `delete` and a bulk `redeliver` ask first; without a terminal they need `--yes`. `redeliver DLV...` takes no bulk
  flags (`--status`, `--since`, `--dry-run`, `--yes`, ...): those go with `--endpoint`.
- Every command takes `--json`. Exit codes: 0 ok, 1 a test or verification failed, 2 usage, 3 setup or server error,
  4 interrupted (Ctrl-C, or "no" to a confirmation).

## Extra headers on facade requests (`FI_EXTRA_HEADERS`)

A Future AGI environment behind a proxy may need its own header on every request: Google IAP, for example, takes an
identity token in `Proxy-Authorization`. Set it once for these clients and tools: the dataset, prompt,
knowledge-base and queue clients, `FutureAGIClient` / `AsyncFutureAGIClient`, `fi.webhooks`, the experiment upload
and read paths, the trace exporter of an uploaded run, and the `futureagi-py` CLI.
This section does not assert `FI_EXTRA_HEADERS` support for the distinct released `fi.Client` / `fi.AsyncClient` family.

```bash
export FI_EXTRA_HEADERS="Proxy-Authorization=Bearer $TOKEN"     # entries: Name=value, separated by ';' or newlines
futureagi-py doctor --offline                                       # "Headers  Proxy-Authorization (from FI_EXTRA_HEADERS ...)"
```

```python
from fi import FutureAGIClient
from fi.webhooks import Webhooks

client = FutureAGIClient(extra_headers={"X-Team": "india"})   # added to FI_EXTRA_HEADERS; wins for the same name
wh = Webhooks(extra_headers="X-Team=india")                    # a string in the same format also works
```

The low-level `fi.api.auth.HttpClient` accepts `allow_insecure_http` as its fourth positional
argument, after `base_url`, `session`, and `default_headers`. Pass extra headers by keyword:
`HttpClient(base_url, extra_headers={"X-Team": "india"})`.

- The headers go only to the client's base URL (same scheme, host and port, a path under it), and not to a judge
  model, a webhook receiver, any other URL, or a redirect to another host.
- `X-Api-Key`, `X-Secret-Key` and `Authorization` are refused: the SDK sends its own. Names must be HTTP tokens, a name
  may appear once, and a value cannot be empty or a bare `Bearer` (an empty `$TOKEN`).
- A control character anywhere (CR, LF, NUL, tab or any other) and a name with `:` or whitespace are refused, so no
  value can add a second header line. In the setting, `;` and newlines separate entries, and each entry is checked.
- Values are not logged, printed, journaled or traced; errors and `doctor` name the header, not its value.
- The setting is read when each request is sent, so `os.environ["FI_EXTRA_HEADERS"] = ...` refreshes a token without a
  new client. The trace exporter of an uploaded run reads it when the run starts.
- A malformed setting raises `fi._extra_headers.ExtraHeadersError` (a `ValueError`) on the first platform request;
  the CLI exits 3 and `futureagi-py doctor` shows the problem.
