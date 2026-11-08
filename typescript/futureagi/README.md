# Future AGI TypeScript SDK <!-- omit in toc -->

The official TypeScript / Node.js client for the **Future AGI** platform.  
Use it to create and manage evaluation datasets, run prompt–template
experiments, build knowledge-bases, and monitor the quality of your
generative-AI models – all from code.

- **Website:** <https://futureagi.com>
- **API docs:** <https://docs.futureagi.com>
- **NPM:** [`@future-agi/sdk`](https://www.npmjs.com/package/@future-agi/sdk)

---

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Two client families](#two-client-families)
- [Authentication](#authentication)
- [Quick-start](#quick-start)
- [API overview](#api-overview)
- [Error handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

---

## Features

• 📊 **Datasets** – create, mutate, download & evaluate tabular datasets.  
• 📜 **Prompt templates** – full CRUD, versioning and execution of
templates (including OpenAI-style chat messages & variables).  
• 📚 **Knowledge-bases** – upload files, list and delete KB assets.  
• ⚙️ **Utilities** – bounded executors, helper constants and strong
TypeScript types for all request / response payloads.  
• 🤝 **Modern build** – ships both **ESM (ES2020)** _and_
**CommonJS (ES2016)** bundles; works in Node 18+ and all modern bundlers.

## Requirements

- Node.js **18 or later** (the SDK targets ES2020 for ESM builds).
- An **API&nbsp;key** and **Secret key** obtained from your Future AGI
  account.

## Installation

```bash
# npm
npm install @future-agi/sdk

# pnpm
pnpm add @future-agi/sdk

# yarn
yarn add @future-agi/sdk
```

The package automatically selects the build that matches your
environment:

| Import style    | Runtime requirement             | File served            |
| --------------- | ------------------------------- | ---------------------- |
| `import … from` | ES modules (Node 18+, browsers) | `dist/esm/**` (ES2020) |
| `require('…')`  | CommonJS (Node 18+)             | `dist/src/**` (ES2016) |

**Gateway client:** for model calls through the Agent Command Center gateway, use `@future-agi/sdk/gateway` (with `/gateway/testing`, `/gateway/express`, `/gateway/nextjs`, and `/gateway/react`, which needs React 17–19), the `@agentcc/client` 1.0 client (and `@agentcc/react` as `/gateway/react`) ported into this package under the same names with some intended behaviour changes, and keep the standalone `@agentcc/client` package only for helpers that were not ported, such as the budget, batch and token utilities.

## Observe queries

Use `client.tracing` on `FutureAGIClient` for projects, sessions, users, spans,
error clusters and dashboards. `spansByTrace(traceId, { project_id: projectId })`
reads one bounded span page and preserves its completeness and cursor metadata.
See the [Observe guide](../../python/fi/tracing/README.md) for examples.
Instrumentation remains in the separate [traceAI](https://github.com/future-agi/traceAI)
`@traceai/*` packages; installing this SDK does not instrument an application.

## Two client families

`Client` and `FutureAGIClient` are distinct classes, not aliases. Use the API and
response contract for the class you instantiate; do not exchange their page or
error types just because the names match.

| Family | Import | Response and pagination contract | Error types |
| --- | --- | --- | --- |
| Released platform client | `Client` from `@future-agi/sdk` or `@future-agi/sdk/platform` | Generated resource methods unwrap their declared result; paginated list methods return an async-iterable `platform.Pager`. `request(..., { unwrap: null })` returns the complete body. | `platform.APIError`, `platform.NotFoundError`, etc. |
| Facade client | `FutureAGIClient` from `@future-agi/sdk` | Core facade methods retain backend response bodies and declared envelopes/pages. Observe and Console facades have their own typed response shapes; follow each method's contract. | Root `FutureAGIAPIError`, `NotFoundError`, etc. from the facade core |

The root `Client` is exactly `platform.Client`. The platform's models are available
from `@future-agi/sdk/platform/models` (or `platform.models`); its errors and paging
remain under `platform` / `@future-agi/sdk/platform`, not flattened into the root.
Root `Page` selects the facade core. Root `RateLimitError` and `ServerError`
retain the legacy dataset constructors; `DatasetRateLimitError` and
`DatasetServerError` are aliases of those same constructors. For facade-core
errors from `FutureAGIClient`, catch `CoreRateLimitError` and `CoreServerError`.

**Simulation:** only the separate Python `fi.simulate` facade is withdrawn from
SDK operation (its clear-error stub points to `fi.alk.simulate`). The released
platform client's `client.simulation` resource remains available in both
languages. It is not replaced by the facade client or by an ALK alias.

## Authentication

Set your credentials as environment variables **once**:

```bash
export FI_API_KEY="YOUR_API_KEY"
export FI_SECRET_KEY="YOUR_SECRET_KEY"
```

…or pass them explicitly when creating a client:

```ts
import { Dataset } from "@future-agi/sdk";

const ds = await Dataset.open("my-dataset", {
  fiApiKey: "YOUR_API_KEY",
  fiSecretKey: "YOUR_SECRET_KEY",
  createIfMissing: true,
});
```

## Quick-start

### Run a deterministic evaluation over REST

Use the evaluation REST API from TypeScript. Set `FI_BASE_URL` to your API
origin and supply a **personal API key and secret created explicitly in your
account**. This example never creates credentials.
`GET /sdk/api/v1/get-evals/` lists the templates and their required input fields.
The example below submits one JSON-validation input; it does not call an LLM.

```ts
async function evaluateJson() {
  const { FI_BASE_URL, FI_API_KEY, FI_SECRET_KEY } = process.env;
  if (!FI_BASE_URL || !FI_API_KEY || !FI_SECRET_KEY) {
    throw new Error("Set FI_BASE_URL, FI_API_KEY and FI_SECRET_KEY");
  }
  const response = await fetch(new URL("/sdk/api/v1/new-eval/", FI_BASE_URL), {
    method: "POST",
    redirect: "error",
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": FI_API_KEY,
      "X-Secret-Key": FI_SECRET_KEY,
    },
    body: JSON.stringify({
      eval_name: "is_json",
      inputs: { output: '{"answer":42}' },
      is_async: false,
    }),
  });
  const data = await response.json();
  if (!response.ok || data.status === false) {
    throw new Error(`Evaluation failed (HTTP ${response.status})`);
  }
  return data.result;
}
```

Call `await evaluateJson()` from your application. A refusal is an error, not
an evaluation score. For asynchronous requests, set `is_async: true` and poll
`GET /sdk/api/v1/new-eval/?eval_id=<returned-id>` for completion.

### The released platform client

`Client` covers the whole platform (158 operations across datasets, prompts, evals, traces, annotation
queues, knowledge bases, gateways, dashboards, ...). It is generated from the API contract, so method
names match the Python SDK and the MCP tools; see `sdkgen/README.md` in the repository.

```ts
import { Client } from '@future-agi/sdk';

const client = new Client();   // FI_API_KEY, FI_SECRET_KEY, FI_BASE_URL (or pass apiKey/secretKey/baseUrl)

const ds = await client.datasets.create({ new_dataset_name: 'qa-set' });
await client.datasets.columns.add(ds.dataset_id!, { new_columns_data: [{ name: 'question', data_type: 'text' }] });
for await (const d of client.datasets.list({ search_text: 'qa' })) console.log(d.name);   // walks every page
await client.fileKnowledgeBases.create({ name: 'docs', file: ['./notes.txt'] });           // multipart upload
await client.datasets.get(ds.dataset_id!, {}, { timeout: 5_000, headers: { 'X-Trace': 't1' } });  // per-call options
await client.request('GET', '/some/new/endpoint/', { query: { page: 1 } });              // anything else, same auth/retries
```

Errors are typed (`platform.NotFoundError`, `platform.BadRequestError`, ...) and carry the backend's `type`,
`code` and `detail`; 429 is retried, and 5xx only for calls that are safe to repeat. Extend the client by
adding methods in `src/platform/resources/<name>.ts` (never regenerated) or passing your own classes:
`new Client({ resources: { datasets: MyDatasets } })`.

The classes below (`Dataset`, `Prompt`, `KnowledgeBase`, ...) keep working unchanged.

### 1. Create a dataset & add rows

```ts
import { Dataset, DataTypeChoices } from "@future-agi/sdk";

async function main() {
  // Open (or create) a dataset
  const ds = await Dataset.open("translations", { createIfMissing: true });

  // Add two columns
  await ds.addColumns([
    { name: "prompt", dataType: DataTypeChoices.TEXT },
    { name: "answer", dataType: DataTypeChoices.TEXT },
  ]);

  // Add a couple of rows
  await ds.addRows([
    { prompt: "Translate “Hello World” to French", answer: "Bonjour le monde" },
    { prompt: "Translate “Good night”  to German", answer: "Gute Nacht" },
  ]);

  console.log("Dataset ready:", ds.getConfig());
}
```

### 2. Create & execute a prompt template

```ts
import { Prompt, MessageBase, ModelConfig } from "@future-agi/sdk";

const prompt = new Prompt();

await prompt.createNewVersion({
  template: {
    name: "translator",
    messages: [
      { role: "system", content: "You are a translator." } as MessageBase,
      { role: "user", content: "Translate {{text}} to French." } as MessageBase,
    ],
    variable_names: { text: "string" },
    model_configuration: new ModelConfig({ model_name: "gpt-3.5-turbo" }),
  },
});

// Run the template with variables
const result = await prompt.template?.run({ text: "Good morning" });
console.log(result);
```

### 3. Build a knowledge base

```ts
import { KnowledgeBase } from "@future-agi/sdk";

const kb = new KnowledgeBase();
await kb.createKb("docs", ["./README.md", "./whitepaper.pdf"]);

const list = await kb.listKbs();
console.log(`You now have ${list.length} knowledge-bases!`);
```

## API overview

```ts
import {
  Dataset, // datasets / evaluations
  KnowledgeBase, // RAG knowledge-bases
  Prompt, // prompt templates
  Client, // released platform resources
  FutureAGIClient, // facade client (a distinct class)
  platform, // released client error, page and model namespace
} from "@future-agi/sdk";
```

See the full **TypeDoc API reference** at  
<https://futureagi.com/docs/sdk/typescript>.

### OpenAPI-backed client

For API surfaces that are generated from the backend OpenAPI contract, use
the wrapper client instead of importing generated files directly:

```ts
import { FutureAGIClient } from "@future-agi/sdk";

const client = new FutureAGIClient({ apiKey: "...", secretKey: "..." });
const queues = await client.annotationQueues.list({ limit: 20 });
const nextItem = await client.annotationQueues.items.next("queue-id");

const datasets = await client.datasets.list({ page: 1 });
const experimentRows = await client.experiments.rows("experiment-id");
const traceProjects = await client.tracing.projects();
const me = await client.users.current();
const alertOptions = await client.alerts.metricOptions({
  project_id: "project-id",
});
```

The low-level generated code is regenerated with `scripts/generate-oss-sdk.sh`.
Public method names are controlled by `openapi/sdk/operation-aliases.json` and
`openapi/sdk/wrapper-map.json`.
Go and Java low-level clients are regenerated with `scripts/generate-go-java-sdk.sh`.

## Error handling

The two client families have separate error trees. Catch the released `Client`'s
errors through its namespace:

```ts
import { Client, platform } from "@future-agi/sdk";

const client = new Client();
try {
  await client.datasets.get("missing-dataset");
} catch (err) {
  if (err instanceof platform.APIError) {
    console.error(err.status, err.code);
  } else {
    throw err;
  }
}
```

The facade core and legacy helper errors extend `SDKException`; this is not the
base class for the released platform client's errors.

```ts
import { Dataset, SDKException } from "@future-agi/sdk";

try {
  await Dataset.open("missing-dataset");
} catch (err) {
  if (err instanceof SDKException) {
    console.error(err.getErrorCode(), err.getMessage());
  } else {
    console.error("Unexpected error", err);
  }
}
```

Common subclasses include:

- `InvalidAuthError` – wrong or missing credentials.
- `DatasetNotFoundError` – dataset name not found.
- `DatasetRateLimitError` – quota exceeded in a legacy dataset call.
- Root `RateLimitError` – quota exceeded in a facade call; released platform calls
  use `platform.RateLimitError` instead.

## Extra headers on every platform request (`FI_EXTRA_HEADERS`)

The same setting as the Python SDK. `FutureAGIClient` and the dataset, prompt, knowledge-base and queue clients add
it to every request to their base URL:

```ts
// FI_EXTRA_HEADERS="Proxy-Authorization=Bearer <identity token>"  (Name=value entries, ';' or newlines between)
const client = new FutureAGIClient({ extraHeaders: { "X-Team": "india" } }); // wins over the setting per name
```

- Only to URLs under the base URL; a redirect never carries them to another host (`FutureAGIClient` does not follow
  redirects while extra headers are in effect).
- `X-Api-Key`, `X-Secret-Key` and `Authorization` are refused with an `ExtraHeadersError` naming the setting; values
  are never put in an error. The setting is read when each request is sent; a malformed one fails at once, never
  retried.
- A control character anywhere (CR, LF, NUL, tab or any other) and a name with `:` or whitespace are refused, so no
  value can add a second header line. `extraHeaders` values never show in `util.inspect`, `console.log` or
  `JSON.stringify` of a client.
- Browsers drop `Proxy-*` request headers: use Node.js for a proxy-authenticated environment. `defaultHeaders` keeps
  working as before.

## Contributing

1. Fork the repo and create your branch from `main`.
2. Run `pnpm i && pnpm test` to ensure the test-suite is green.
3. Submit a pull-request – please include unit tests for new behaviour.

See `CONTRIBUTING.md` at the project root for more details.

## License

This project is distributed under a BSD-style license – see
[LICENSE.md](../../LICENSE.md) for the full text.

### Dataset versions and external experiment runs (draft)

`FutureAGIClient` exposes six typed methods backed by the generated client:

- `client.datasets.versions.list(datasetId, { limit, offset })`
- `client.datasets.versions.get(datasetId, versionId, { limit, offset })`
- `client.datasets.versions.create(datasetId, body)`
- `client.experimentRuns.create(body)`
- `client.experimentRuns.ingestResults(runId, { items })`
- `client.experimentRuns.compare(body)`

The backend owns the request and response shapes. These APIs require core PRs #3473–#3475 and are not yet claimed as a released SDK capability. You execute agent tasks and scorers in your process, then upload results with stable example/trial identities and pinned metric/version references.

Each call makes one HTTP attempt. Snapshot creation is not idempotent; do not blindly retry an ambiguous timeout. Run/result replay is safe only with the same UUID or receipt keys and unchanged payload. Conflicts and parse failures surface to the caller without a second request.

`examples/dataset-experiment-lifecycle.ts` demonstrates the deterministic end-to-end flow. Nullable outputs and trace references are preserved; no model or live Observe integration is implied.

For per-example trial counts, observed score spread, and paired deltas, opt in on
the existing comparison call (requires core PR #3483):

```typescript
const report = await client.experimentRuns.compare({
  baseline_run_id: baselineRunId,
  candidate_run_id: candidateRunId,
  metric_id: metricId,
  include_trial_stability: true,
});
for (const example of report.result.trial_stability ?? []) {
  console.log(example.example_id, example.candidate.score_stddev);
}
```

The optional `trial_stability` result is `undefined` when the backend omits it.
Nullable statistics remain `null`; a standard deviation of `null` means fewer
than two assessed values, while `0` means observed zero spread. This is
descriptive analysis, not statistical significance. It can be requested with
`release_gate` without changing the gate's verdict.

### Webhooks: verify a request

Future AGI signs every webhook request with [Standard Webhooks](https://www.standardwebhooks.com/) v1.
`verifyWebhook` checks the signature over the **raw** body and the timestamp (300 s), and returns the event:

```ts
import express from "express";
import { verifyWebhook, WebhookVerificationError } from "@future-agi/sdk/webhooks";

const app = express();
app.post("/hook", express.raw({ type: "application/json" }), (req, res) => {
  try {
    const event = verifyWebhook({ body: req.body, headers: req.headers, secret: process.env.FI_WEBHOOK_SECRET! });
    if (event.test) return res.sendStatus(200);
    // handle event.type; dedupe on event.id (delivery is at least once)
    return res.sendStatus(200);
  } catch (err) {
    if (err instanceof WebhookVerificationError) return res.sendStatus(400); // err.reason says why
    throw err; // WebhookSecretError: a malformed secret is a server error, so the delivery is retried
  }
});
```

In a fetch handler pass `await request.text()` and `request.headers`. `@future-agi/sdk/webhooks` loads only the
verifier (Node's `crypto`); the same names are exported from the package root. `signWebhook` and
`webhookSignatureHeader` build signed requests for your own tests.

Creating and managing webhook endpoints from TypeScript is not in this release. Use the Python SDK (`fi.webhooks`),
the `futureagi-py webhooks` CLI or the REST API. `@future-agi/sdk/webhooks` provides both ESM and CommonJS
entrypoints through the package's `import` and `require` conditions.
