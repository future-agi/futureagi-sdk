# Future AGI TypeScript SDK <!-- omit in toc -->

The official TypeScript / Node.js client for the **Future AGI** platform.  
Use it to create and manage evaluation datasets, run prompt–template
experiments, build knowledge-bases, and monitor the quality of your
generative-AI models – all from code.

* **Website:** <https://futureagi.com>  
* **API docs:** <https://docs.futureagi.com>  
* **NPM:** [`@future-agi/sdk`](https://www.npmjs.com/package/@future-agi/sdk)

---

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
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
• 🤝 **Modern build** – ships both **ESM (ES2020)** *and*
  **CommonJS (ES2016)** bundles; works in Node 18+ and all modern bundlers.

## Requirements

* Node.js **18 or later** (the SDK targets ES2020 for ESM builds).  
* An **API&nbsp;key** and **Secret key** obtained from your Future AGI
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

| Import style       | Runtime requirement | File served                |
| ------------------ | ------------------- | -------------------------- |
| `import … from`    | ES modules (Node 14+, browsers) | `dist/esm/**` (ES2020) |
| `require('…')`     | CommonJS (all Node versions)    | `dist/src/**` (ES2016) |

## Authentication

Set your credentials as environment variables **once**:

```bash
export FI_API_KEY="YOUR_API_KEY"
export FI_SECRET_KEY="YOUR_SECRET_KEY"
```

…or pass them explicitly when creating a client:

```ts
import { Dataset } from '@future-agi/sdk';

const ds = await Dataset.open('my-dataset', {
  fiApiKey: 'YOUR_API_KEY',
  fiSecretKey: 'YOUR_SECRET_KEY',
  createIfMissing: true
});
```

## Quick-start

### 0. The platform client (every API, one object)

`Client` covers the whole platform (283 operations across Skills, contexts, datasets, prompts, evals, traces, annotation
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
import { Dataset, DataTypeChoices } from '@future-agi/sdk';

async function main() {
  // Open (or create) a dataset
  const ds = await Dataset.open('translations', { createIfMissing: true });

  // Add two columns
  await ds.addColumns([
    { name: 'prompt',  dataType: DataTypeChoices.TEXT },
    { name: 'answer',  dataType: DataTypeChoices.TEXT }
  ]);

  // Add a couple of rows
  await ds.addRows([
    { prompt: 'Translate “Hello World” to French', answer: 'Bonjour le monde' },
    { prompt: 'Translate “Good night”  to German', answer: 'Gute Nacht'      }
  ]);

  console.log('Dataset ready:', ds.getConfig());
}
```

### 2. Create & execute a prompt template

```ts
import { Prompt, MessageBase, ModelConfig } from '@future-agi/sdk';

const prompt = new Prompt();

await prompt.createNewVersion({
  template: {
    name: 'translator',
    messages: [
      { role: 'system', content: 'You are a translator.' } as MessageBase,
      { role: 'user',   content: 'Translate {{text}} to French.' } as MessageBase
    ],
    variable_names: { text: 'string' },
    model_configuration: new ModelConfig({ model_name: 'gpt-3.5-turbo' })
  }
});

// Run the template with variables
const result = await prompt.template?.run({ text: 'Good morning' });
console.log(result);
```

### 3. Build a knowledge base

```ts
import { KnowledgeBase } from '@future-agi/sdk';

const kb = new KnowledgeBase();
await kb.createKb('docs', ['./README.md', './whitepaper.pdf']);

const list = await kb.listKbs();
console.log(`You now have ${list.length} knowledge-bases!`);
```

## API overview

```ts
import {
  Dataset,          // datasets / evaluations
  KnowledgeBase,    // RAG knowledge-bases
  Prompt,           // prompt templates
  constants,        // misc constants
  errors            // rich error classes
} from '@future-agi/sdk';
```

See the full **TypeDoc API reference** at  
<https://futureagi.com/docs/sdk/typescript>.

## Keys over plain http

A request that carries your key (`X-Api-Key`, `X-Secret-Key`, `Authorization` and the other credential headers) is
not sent over plain http to a host that is not loopback (`localhost`, `127.0.0.0/8`, `::1`). The call rejects before
any connection is made with an `Error` whose `code` is `insecure_http_origin`, and the client does not retry it:

```ts
try {
  await kb.listKbs(); // any call of a client that sends your key
} catch (err) {
  if ((err as { code?: string }).code === 'insecure_http_origin') {
    // use an https:// base URL, or opt in to plain http
  }
}
```

To send keyed requests over plain http to such a host, set `allowInsecureHttp: true` in the client options, or set
`FI_ALLOW_INSECURE_HTTP=1` when the option is not given. An explicit `allowInsecureHttp: false` wins over the
variable. A request that carries your key does not follow redirects: on `HttpClient` and the classes built on it a
3xx response rejects with `UnexpectedRedirectError` (code `UNEXPECTED_REDIRECT`), and on the platform `Client` with
an `APIConnectionError`, for a redirect to the same origin as well. Configure the final address of the endpoint as
the base URL. A keyed `HttpClient` request does not use the Axios `proxy` option. A `Proxy-Authorization` header in a
call's headers, default headers or `fetchOptions` goes to a proxy alone (see
[Upgrading from 0.3 to 0.4](#upgrading-from-03-to-04)). A keyed request goes through an Axios adapter of your own
only with `customAdapterReceivesKeys: true`, and through a `fetch` of your own given to the platform `Client` only
with `customFetchReceivesKeys: true`. The SDK checks where a request goes before your own adapter or `fetch` runs; a
change that code makes afterwards (another adapter, a proxy, a URL, agent or DNS lookup) is not checked again. See the
[CHANGELOG](https://github.com/future-agi/futureagi-sdk/blob/main/typescript/futureagi/CHANGELOG.md) for the details.

## Upgrading from 0.3 to 0.4

### Breaking: `Proxy-Authorization` goes to a proxy alone
A `Proxy-Authorization` header (any letter case, in any header container) in a call's headers, a client's default
headers, `fetchOptions.headers` or one that an interceptor adds is withheld from every send that reaches its host: a
keyed request, a host that `NO_PROXY` names, a request with no proxy, Axios's `fetch` adapter, an adapter function,
and the platform `Client`. Only a plain `http://` `HttpClient` request sent through the proxy named in its Axios
`proxy` option carries it. A request that the proxy environment routes, and an `https://` request, which goes through
a CONNECT tunnel (Axios's, the runtime's environment proxy, or a proxy agent or dispatcher of yours), carry none,
where 0.3.1 sent a per-call value to the environment proxy.

Migration: give proxy credentials in the proxy URL (`HTTP_PROXY=http://user:password@proxy:port`), in the `proxy`
option's `auth`, or to the agent or dispatcher.

### Added: extra headers on every request to the base URL (`FI_EXTRA_HEADERS`, `extraHeaders`)
`HttpClient` and the dataset, prompt, knowledge-base, annotation and queue clients built on it add the
`FI_EXTRA_HEADERS` setting (`Name=value` entries separated by `;`, CR or LF) to every request to their base URL, for
example a `Proxy-Authorization` for a reverse proxy such as Google IAP. `HttpClient` also takes an `extraHeaders`
option (a record, or text in the same format) that wins over the setting for the same name:

```ts
// FI_EXTRA_HEADERS="Proxy-Authorization=Bearer <identity token>"
```

- They go only to URLs under the base URL, and a redirect does not carry them to another host.
- `X-Api-Key`, `X-Secret-Key`, `Authorization`, `X-Workspace-Id` and `X-Organization-Id` are refused with an
  `ExtraHeadersError` (exported from `@future-agi/sdk`, with `EXTRA_HEADERS_ENV`) naming the setting; values are not
  put in an error or in `util.inspect` output.
- Browsers drop `Proxy-*` request headers: use Node.js for a proxy-authenticated environment.

### Breaking: per-call header containers merge with client defaults
`HttpClient.request` merges a per-call list of header pairs, a `Map`, a `Headers` object or another supported
non-record container with the client's default headers. In 0.3.1 these containers replaced the defaults.
An empty list or `null` also retains client headers, including `X-Api-Key` and `X-Secret-Key` if configured.

Migration: pass a plain object to override individual defaults by name. In JavaScript, set each default you want
omitted to `undefined` in that object. In TypeScript, `headers` takes string values; use a client without those defaults.

### Breaking: keyed requests refuse same-origin redirects
A request carrying API keys refuses a redirect, even when the destination has the same
origin. Call the final URL directly instead of using a URL that redirects. With `customAdapterReceivesKeys: true`,
an Axios adapter other than Axios's `http` adapter (one of your own, or Axios's `fetch` or `xhr`) decides itself
whether to follow a redirect.

### Breaking: `ProviderAPIKeyClient` takes a boolean after `fiBaseUrl`
In `new ProviderAPIKeyClient(apiKey, fiApiKey, fiSecretKey, fiBaseUrl, customAdapterReceivesKeys)`, the final
argument replaces the options object. Any value other than `true`, `false` or `undefined` (an options object
included) throws a `TypeError` that names `customAdapterReceivesKeys`. Omit the argument or pass `false`
to keep keys out of custom adapters. Pass `true` to opt in when you own the adapter and want it to receive keys.

### Breaking: a `fetch` of your own receives keys only with `customFetchReceivesKeys: true`
The platform `Client` sends keyed calls through a `fetch` you pass (or a `globalThis.fetch` replaced after the SDK
loaded) only with `customFetchReceivesKeys: true`; without it the call is refused before any connection with code
`custom_fetch_not_opted_in`. With it, the destination rules apply to that `fetch` and the proxy rules do not.
These rules also apply to a `Client` given explicit `auth`, a Context credential included. Such a client
rejects an authentication or `Proxy-Authorization` header override, and refuses a base URL with user info when it
is built.
`HttpClient` and the classes built on it take `customAdapterReceivesKeys` for an Axios adapter of your own.
The static methods of `ProviderAPIKeyClient`, `APIKeyManager.getInstance` and `getAPIKeyManager` take
`customAdapterReceivesKeys` in their options in place of `allowInsecureHttp`; plain http to a host that is not
loopback follows `FI_ALLOW_INSECURE_HTTP=1`. `ConfigurationError` and `UnexpectedRedirectError` are exported from
`@future-agi/sdk`.

### Other changes
- A request that carries your key to a base URL that writes user info (`user:password@host`) is refused with
  `insecure_http_origin` before any connection. Put credentials in the key options, not in the URL.
- The platform `Client` raises `WrongRegionError` (a `PermissionDeniedError`, code `wrong_region`) for a 403
  `wrong_region` response, and `client.usage.overview` raises `UsageOverviewUnavailableError` for a 404.
- The default request timeout of the dataset, prompt, knowledge-base, annotation and queue clients is 30 seconds
  (Axios measures it in milliseconds; 0.3.1 set 200 ms).
- Prompt templates: `generate`, `improve` and `create`; the template GET and DELETE routes end in `/`.
  `generate()` and `improve()` resolve to a `PromptGenerationResult`. The server runs generation as a job and
  answers with the job id only, so the result holds `jobId`, the SDK does not receive the generated text and the
  template's messages stay as they are; set the message content yourself or generate the prompt in the Future AGI
  app. A server that answers with the text gives `prompt`, which replaces the content of the last message (or
  becomes a user message when the template has none).
- Annotation queues: `getOrCreateDefault(scope)`, and `labelIds`, `autoAssign`, `annotatorIds` and `annotatorRoles`
  on create.
- Responses of the dataset, knowledge-base, annotation and queue clients carry the camelCase field names of earlier
  releases as deprecated aliases of the snake_case fields.

See the [CHANGELOG](https://github.com/future-agi/futureagi-sdk/blob/main/typescript/futureagi/CHANGELOG.md) for the
release notes.

## Error handling

All SDK-specific failures extend `SDKException`.

```ts
import { SDKException } from '@future-agi/sdk/dist/src/utils/errors';

try {
  await Dataset.open('missing-dataset');
} catch (err) {
  if (err instanceof SDKException) {
    console.error(err.getErrorCode(), err.getMessage());
  } else {
    console.error('Unexpected error', err);
  }
}
```

Common subclasses include:

* `InvalidAuthError` – wrong or missing credentials.  
* `DatasetNotFoundError` – dataset name not found.  
* `RateLimitError` – API quota exceeded.

## Skill and agent-context traces

Preview source build only. The current registry version does not certify these APIs.

A load is recorded on the first read of any file of a skill version inside a
recording trace. **Loaded** means verified bytes were given to the app, not that
a model followed them. Fetches, linked skills, delivery and loads are different
facts. A cached snapshot is not evidence of a new load until application code
reads or explicitly reports it during a traced request.

The SDK does not install OpenTelemetry, a provider, an exporter, a context
manager or a propagator. It probes the already-registered OTel API global on
each read, so registering OTel after importing the SDK works. The API peer is
optional and imports work without it. With a global provider, reads record
loads without application changes. To name an agent, wrap its request:

```ts
import { withAgentScope, declareSkill } from '@future-agi/sdk/telemetry';

await withAgentScope({ agent: 'refund-agent' }, async () => {
  // Start the request's root span inside this callback.
  const skill = await skills.resolve('refund', { label: 'production' });
  const policy = await skill.readFile('SKILL.md');
  // Give policy to application code here.
});
```

For **vanilla OTel JS**, also list `new FutureAGISkillsSpanProcessor()` from
`@future-agi/sdk/telemetry` in the provider constructor's `spanProcessors`
list, alongside the application's exporter processor. Do not replace that
exporter. OTel JS 2.x cannot add processors after construction.

With **traceAI** (`@traceai/fi-core`), skill and agent-context attribution is
opt-in per provider. Pass `runtimeAttributes: true` to `register()` (or to the
provider), or list traceAI's `FutureAGIRuntimeAttributesSpanProcessor` in
`spanProcessors`; do not install both processors:

```ts
import { register } from '@traceai/fi-core';

const provider = register({ projectName: 'support', runtimeAttributes: true });
```

Without that opt-in the provider installs no runtime processor, and its spans,
contexts and exports are unchanged. `configure()` cannot opt a provider in; on a
provider that opted in it can only narrow behaviour (`'off'`, `'load_only'`).
Listing only `FutureAGISkillsSpanProcessor` on a traceAI provider stamps later
spans, but it does **not** enable traceAI's span identity calls; those run only
on spans started by a provider that opted in. Agent identity read back from a
traceAI span is always PII-redacted.

No code to record the load. One scope line names the agent; the provider must
also have the processor to stamp later spans. This is not a claim that every
already-started span can be changed.

### Controls and diagnostics

```ts
import { configure, status } from '@future-agi/sdk/telemetry';
configure({ skillsTracing: 'load_only', tracerProvider: applicationProvider });
// Modes: 'on' (default), 'load_only' (load spans only), 'off'.
console.log(status());
```

`FI_SKILLS_TRACING=off` disables tracing and its info logs;
`FI_SKILLS_TRACING=load_only` emits only loads, without current-span enrichment,
shared attribution registry or stamping. Programmatic configuration wins over
the environment; `configure()` clears programmatic overrides. First reads log
one informational diagnostic per setup, never credentials, contents or paths.

Run `npx --package=@future-agi/sdk futureagi-telemetry doctor`, or the installed
`futureagi-telemetry doctor` binary. A new CLI process cannot inspect the provider
in another running process: call `status()` inside the app to diagnose it.
Doctor redacts app-supplied identity values. `processor_installed` is conservative:
it confirms a processor just observed the current trace, not installation on
all providers. The present implementation cannot distinguish traceAI's global
provider from vanilla OTel; that truth-table diagnostic still requires integration.

### Reference and evidence

- `new SkillsClient(clientOrSource, { tracing: false })` and
  `new ContextClient(client, { tracing: false })` opt out per client.
- `snapshot.readFile(path, { trace: false })` and
  `snapshot.readAll({ trace: false })` opt out per call.
- `declareSkill(snapshot)` or `declareSkill(lock)` records **Reported by the app**
  evidence. `LockedSkill` is an explicit, typed declaration with kind, name,
  resourceId, versionId, version, digest and requested selector. It does not
  verify external files. Ordinary SDK reads record **Given to the app** evidence.
- A first supporting-file read records a load with `root_file: false`. A later
  root read of the same version/evidence in the same scope does not add a load.
- `readAll()` suppresses its inner file reads per call, including concurrent
  reads. A skill `readAll()` records one load; a context `readAll()` records only
  `context.load`, with linked versions available but not loaded.
- Integrity, authorization, lease and not-found failures remain consumption
  errors. Failed `skill.load` spans have error category, reported name and
  selector, never an unverified skill id, version id or digest. They are not loads.
- Resolves, manifest pages, authorization checks, authoring, and generated
  low-level `client.skills` / `client.skillConsumption` operations are untraced.
  Use high-level clients for runtime attribution.
- The user agent includes the SDK version. Only consumption resolve adds
  `X-FI-Skills-Tracing: on | load_only | off | no_otel`.

| Capability | TypeScript | Python |
| --- | --- | --- |
| High-level skill/context reads | Available | Available |
| Scope helper / explicit declaration | `withAgentScope` / `declareSkill` | `agent_scope` / `declare_skill` |
| Vanilla OTel later-span stamping | Constructor processor required | Additive processor installation |
| Installer, context sessions, Deep Agents adapter | Not present in this package | Python integrations |

### Propagation limits and integration gaps

Automatic mode shares a bounded 4,096-trace, one-hour registry. Several agents
interleaved in one trace share its list: use explicit scopes to separate them.
Lists cap at 32 versions and set `fi.skills.truncated` after that. Evidence
is deduplicated per version and evidence level; failed reads per reported name,
selector and error category. `load_only` keeps private, bounded-lifetime evidence
state for deduplication but never publishes it to the propagation registry.

A nested context replaces context identity and resets skill lists; a plain nested
scope inherits and appends to its own list. Scope exit restores its parent on
success, exception or async rejection. The OTel context manager must already be
installed and support async propagation. Thread/worker or process handoff needs
explicit context capture/binding. Head-sampled-out spans do not record loads.
Already-started ancestor spans cannot be retroactively stamped. Explicit scopes
never mutate a shared outer span; automatic mode enriches only the current span.

**Lazy linked reads remain incomplete.** Today's `SnapshotManifest` has no
verified `LockedLink` identities. A context `readAll()` verifies the descriptor
and all child digests and remembers that closure without additional I/O. Later
direct child reads then record the child's verified identity. A direct child read
before that verification records no load, and a root-only `AGENTS.md` read cannot
supply `linked_skill_version_ids`. An empty list is not fabricated. Consumption
must provide verified closure metadata before this is complete; failed child
reads before closure verification cannot be reliably attributed to a child.
Telemetry must not fetch extra files to hide this gap.

The SDK/traceAI TypeScript registry ABI used here is
`globalThis[Symbol.for('futureagi.runtime.skills.v1')]` with `v: 1` and
`get(traceId)` returning allowlisted attributes or `undefined`. Carriers use
`Symbol.for('futureagi.runtime.span_attributes.v1')`; each read of a scope's
context yields an immutable `{ v: 1, attrs, reset_skills }` value. The fi-core
processor must pass the copied Python conformance vectors and read this same
registry ABI before the integration is qualified.

All runtime, packaging and provider tests for this change require cloud
qualification. No local execution is a substitute for that gate.

## Contributing

1. Fork the repo and create your branch from `main`.  
2. Run `pnpm i && pnpm test` to ensure the test-suite is green.  
3. Submit a pull-request – please include unit tests for new behaviour.

See `CONTRIBUTING.md` at the project root for more details.

## License

This project is distributed under a BSD-style license – see
[LICENSE.md](../../LICENSE.md) for the full text.