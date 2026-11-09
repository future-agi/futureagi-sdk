# sdkgen: Python SDK and TypeScript SDK from one contract and one catalog

`sdkgen` generates the platform client for both SDKs (`fi.Client` in Python, `new Client()` in TypeScript) from the backend's API contract plus a small catalog. The catalog records, for each operation, the MCP tool it corresponds to in the monorepo (`futureagi/mcp_server/catalog/tools.yaml`), so an operation has the same name in the SDKs and in MCP; the MCP server itself is generated and served from the monorepo, not here.

It covers the operations behind the pinned backend's MCP tools (same names), the
SDK-only dataset/prompt/KB/queue/annotation surface, and F12 isolated context/leaf
consumption. The catalog parity gate checks exact MCP tool-name agreement; snapshot,
installer and runtime adapters reuse these generated operations and the shared transport.

```
future-agi/api_contracts/openapi/swagger.json ──sync_contract.py──▶ sdkgen/contracts/swagger.json
                                                                    sdkgen/catalog/operations.yaml
                                                                            │
                                                                    sdkgen/generate.py  (CLI)
                                                                    sdkgen/generator/   (catalog.py → python.py, typescript.py)
                        ┌───────────────────────────────────────────────────┼───────────────────────────────────────┐
     python/fi/platform/models.py                          typescript/futureagi/src/platform/models.ts      (public: response models)
     python/fi/platform/resources/base.py                  typescript/futureagi/src/platform/resources/base.ts    (public: resource base classes)
     python/fi/platform/_operations.py                     typescript/futureagi/src/platform/_operations.ts       (one Operation per call)
     python/fi/platform/resources/__init__.py              typescript/futureagi/src/platform/resources/index.ts
                        │                                                   │
     hand-written: python/fi/platform/{_client,_transport,_pagination,_errors,_resource}.py
                   python/fi/platform/resources/<name>.py          (scaffolded once, then yours)
                   typescript/futureagi/src/platform/{client,transport,pagination,errors,resource}.ts
                   typescript/futureagi/src/platform/resources/<name>.ts   (scaffolded once, then yours)
```

## What users get

```python
from fi import Client

client = Client()   # FI_API_KEY, FI_SECRET_KEY, FI_BASE_URL

ds = client.datasets.create(new_dataset_name="qa-set")               # models.DatasetCreateStartedResult
client.datasets.columns.add(ds.dataset_id, new_columns_data=[{"name": "question", "data_type": "text"}])
client.datasets.rows.add(ds.dataset_id, rows=[{"cells": [{"column_name": "question", "value": "2+2?"}]}])  # beta
table = client.datasets.get(ds.dataset_id)                           # models.DatasetTableResult
for d in client.datasets.list(search_text="qa"):                     # walks every page
    print(d.name)
client.datasets.delete(dataset_ids=[ds.dataset_id])
```

```ts
import { Client } from "@future-agi/sdk";

const client = new Client();   // FI_API_KEY, FI_SECRET_KEY, FI_BASE_URL

const ds = await client.datasets.create({ new_dataset_name: "qa-set" });
await client.datasets.columns.add(ds.dataset_id!, { new_columns_data: [{ name: "question", data_type: "text" }] });
for await (const d of client.datasets.list({ search_text: "qa" })) console.log(d.name);
await client.fileKnowledgeBases.create({ name: "docs", file: ["./notes.txt", { name: "a.txt", data: "..." }] });
```

- **Shared config:** keys and base URL are set once on the client.
- **Async:** Python's `AsyncClient` has the same methods (`await`, `async for`); the TypeScript client is async throughout.
- **Envelope removed:** the backend's `{status, result}` wrapper is unwrapped before you get the result.
- **Typed errors:** `BadRequestError`, `NotFoundError`, `AuthenticationError`, ..., carrying the backend's `type`, `code` and `detail`.
- **Retries:** 429 is retried for every call. Timeouts, 5xx and dropped connections are retried only for calls that are safe to repeat (GET, PUT, DELETE), so a POST the server already applied is never sent twice.
- **Your own HTTP client:** `Client(http_client=...)` (httpx) in Python, `new Client({ fetch })` in TypeScript; used as given.
- **Redirects stay home:** a redirect is followed only within the client's own origin (up to 5 hops; 303 and a redirected POST become GET). One that leaves the origin raises `APIConnectionError`, because the API keys travel in custom headers that neither httpx nor browsers strip on a cross-origin redirect.
- **Omitted vs. null:** every optional argument defaults to `NOT_GIVEN` (`fi.platform.NOT_GIVEN`) and is left out of the request; an explicit `None` is sent as JSON `null`, which is how a nullable field is cleared (`client.prompts.update(id, prompt_folder=None)`). TypeScript: `undefined` is left out, `null` is sent. Query strings and form fields have no null, so there `None` is dropped too.
- **Headers merge case-insensitively:** defaults < client `default_headers` < per-call `options.headers`, and `x-workspace-id` replaces `X-Workspace-Id` instead of being sent next to it.
- **Same names on every surface:** `client.datasets.rows.add` / `client.datasets.rows.add()` / MCP `add_dataset_rows` come from one catalog id. TypeScript uses camelCase for resources and methods (`client.knowledgeBases.createFromFile`) and keeps the wire names for fields, so a request looks the same in both languages and in the API docs.
- **Old code still works:** the existing modules (`fi.datasets.Dataset`, `fi.queues`, the TypeScript `Dataset` class, ...) are untouched.

`client.<resource>`: `account`, `workspaces`, `datasets` (`.columns`, `.rows`, `.cells`, `.evals`, `.prompts`), `knowledge_bases`, `file_knowledge_bases` (`.files`), `prompts` (`.versions`, `.labels`), `evals` (`.templates`, `.groups`, `.tasks`, `.configs`), `projects`, `traces` (`.properties`), `spans`, `sessions`, `alerts` (`.logs`, `.rules`), `error_clusters`, `annotations` (`.labels`), `annotation_queues` (`.items`), `scores`, `experiments`, `optimizations`, `agents` (`.versions`), `simulation` (`.scenarios`, `.tests`, `.executions`), `gateway` (`.request_logs`, `.guardrail_rules`, `.sessions`), `dashboards` (`.widgets`, `.metrics`), `models`, `provider_keys`, `usage`.

See `python/examples/platform_client.py` for a runnable tour.

## Context credentials and immutable continuation

The shared transport supports isolated **consume/report** credentials. This is transport
support, not a claim that the Context backend, snapshot client, installer or native adapter
is enabled or released. Purpose, typed resource grants and lease validity are server-enforced.
Use a separate client for each credential; a report credential cannot retrieve content.

```python
from fi.platform import Client, AsyncClient, ApiKeyAuth, ContextAuth, RequestOptions

client = Client(auth=ContextAuth(credential), workspace_id=workspace_id)
async_client = AsyncClient(auth=ContextAuth(credential), workspace_id=workspace_id)
# Existing explicit pair, without environment fallback:
platform_client = Client(auth=ApiKeyAuth(api_key, secret_key))

# resolution_id and resolution_expires_at are returned by resolve/session responses.
# immutable_path must name the resolved UUID/version, never the moving label.
page = client.request("GET", immutable_path,
    query={"file_offset": next_file_offset},
    options=RequestOptions(resolution_id=resolution_id))
zip_bytes = client.request("GET", immutable_download_path, decode="bytes",
    options=RequestOptions(resolution_id=resolution_id))
# async_client.request has the same arguments, awaited.
```

```ts
import { Client, type Auth, type RequestOptions } from "@future-agi/sdk";

const auth: Auth = { type: "context", credential };
const client = new Client({ auth, workspaceId });
const options: RequestOptions = { resolutionId };
const page = await client.request("GET", immutablePath,
  { query: { file_offset: nextFileOffset } }, options);
const zipBytes = await client.request("GET", immutableDownloadPath,
  { decode: "bytes" }, options); // Uint8Array, not decoded text
```

- Explicit `auth` cannot be combined with top-level API/secret keys. Context mode never
  reads `FI_API_KEY`, `FI_SECRET_KEY` or `FI_WORKSPACE_ID`; base URL configuration remains
  unchanged. Supply the workspace explicitly when desired; the credential already binds scope.
- Explicit auth rejects Authorization, X-Api-Key, X-Secret-Key, Proxy-Authorization and
  Cookie overrides, case-insensitively. Context workspace overrides must match the explicit
  workspace. Python injected HTTP clients must have no auth/default credential headers/cookies;
  these checks run again before each send. Fetch uses `credentials: "omit"` in explicit mode.
  Custom HTTP clients, hooks and fetch implementations remain trusted transport boundaries.
- `RequestOptions(resolution_id=..., idempotency_key=...)` / `{resolutionId, idempotencyKey}`
  send `X-Context-Resolution` / `Idempotency-Key`. Conflicting typed/header values fail;
  no key is generated by the transport. Retries preserve the original identity. An uncertain
  POST is not automatically replayed even when the caller supplied an operation key.
- Resolve once; retain both lease fields and immutable identity. Pass the lease on every
  immutable manifest/chunk/download/access-check request. The transport has no content cache,
  automatic lease renewal, label fallback or 304-to-success conversion. Expiry, revocation
  and quarantine errors retain their code/detail. On expiry, discard incomplete staging and
  re-resolve/replan, or use a separately qualified exact-session renewal; never combine pages.
- Context credentials and leased requests refuse redirects, even same-origin ones. Use the
  canonical trailing-slash endpoint. Existing legacy paired-key clients retain header-override
  and same-origin redirect behavior.
- Leaf-granted consumption uses `/model-hub/skills/consumption/`, not broad legacy routes.
  High-level inventory/hash checking and installation belong above this shared transport.

### Catalog groundwork

OpenAPI `in: header` string parameters support only `Idempotency-Key` and
`X-Context-Resolution`. Both emitters expose `idempotency_key` and `resolution_id`
arguments/params, preserve requiredness, and map them through a validated header helper.
Auth/scope/arbitrary headers, duplicate headers and argument collisions fail generation.
`operation.decode: bytes` generates `bytes` / `Promise<Uint8Array>` downloads; 202-only
operations use the actual accepted-response model.

The pinned F12 contract provides `contexts` and `skill_consumption` (TypeScript:
`skillConsumption`) resolve/manifest/read-file/access-check resources, plus
`context_credentials` (`contextCredentials`) issue/list/revoke. Credential administration
uses ordinary human-bound admin authentication, not a consume token. Issuance requires a
caller-retained `idempotency_key`; a replay returns the same ID without its one-time secret.
`contracts/SOURCE.json` identifies the exact unreleased backend commit and source hashes;
`contracts/mcp-tools.json` pins its generated tool names for offline parity checks. Sync both
with `sync_contract.py SOURCE --backend-commit SHA --mcp-tools TOOLS`. A subsequent released
sync clears the commit-specific metadata. No unavailable ZIP/session/report/proposal/campaign
operation is advertised.

## Snapshot and installer integration (unreleased preview)

The branch packages `fi.context`, `fi.skills`, `@future-agi/sdk/context` and
`@future-agi/sdk/skills`. `ContextClient` and `SkillsClient` are also exported from
the npm root. The Python wheel remains 0.7.0 and the npm package remains 0.2.0;
these are **unpublished branch builds**, not versions to advertise as released
Context support. The backend consumption feature remains disabled pending release qualification.

```python
from fi.platform import Client, ContextAuth
from fi.context import ContextClient

with Client(auth=ContextAuth(credential), base_url=origin,
            workspace_id=workspace_id) as platform:
    snapshot = ContextClient(platform).resolve("team-policy", label="production")
    verified = snapshot.read_all()
    instructions = verified.files["AGENTS.md"]
```

`AsyncContextClient` has awaited `resolve`, `read_file` and `read_all` counterparts.
TypeScript uses `new ContextClient(platform).resolve(name, selector?)`, followed by
`readFile(path)` or `readAll()`. All clients enumerate complete manifest pages,
verify per-file and complete snapshot hashes, preserve the original requested
selector and lease, and fail rather than return partial files or renew a lease.
The caller owns the platform client. There is no content cache.

`SkillsClient(platform)` / `AsyncSkillsClient(platform)` use the same verified engine
through the generated isolated leaf facade, never legacy broad-key Skills routes.
Custom `SnapshotSource` / `AsyncSnapshotSource` adapters remain supported, with their own
live authorization responsibility. Both kinds consume F12 `resource_id`/`kind` manifests
and require all chunk identity fields. Short chunks caused by JSON escaping are accepted
only with contiguous progress, exact byte totals and matching final hashes.

`client.check_access(snapshot.identity, snapshot.manifest.lease)` (async: await it;
TypeScript: `checkAccess`) checks the exact version/digest and the original live lease.
It does not renew authorization or report installation/delivery. Use this callable as
the Python read-only backend's `authorize` argument, not a cached permission decision.

### CLI and environment

Online context commands require all four environment variables:
`FI_CONTEXT_ORIGIN` (HTTPS API origin), `FI_CONTEXT_ORGANIZATION_ID`,
`FI_CONTEXT_WORKSPACE_ID`, and `FI_CONTEXT_CREDENTIAL`. The last is a secret;
provision it privately in the process environment, never in arguments, locks,
source, CI output or screenshots. Stale `FI_API_KEY` / `FI_SECRET_KEY` variables
are ignored. Registry scope must match the reviewed lock/plan.

Run from outside an untrusted project, with the project path explicit. These
commands describe the actual branch CLI, not a released install recipe:

```sh
python -I -m fi.context plan --name team-policy --version 1 --client codex \
  --project /path/to/project --out /private/context-plan.json --allow-preview
python -I -m fi.context inspect --plan /private/context-plan.json
# --diff is an explicit opt-in to print bounded source/local instruction text.
python -I -m fi.context apply --plan /private/context-plan.json --quiescent
python -I -m fi.context verify --lock /path/to/project/.futureagi-context.lock.json
python -I -m fi.context doctor --project /path/to/project
python -I -m fi.context update --lock /path/to/project/.futureagi-context.lock.json --check
python -I -m fi.context update --lock /path/to/project/.futureagi-context.lock.json \
  --plan /private/update-plan.json --allow-preview
python -I -m fi.context restore --lock /private/retained-context.lock.json \
  --project /path/to/project --plan /private/restore-plan.json --allow-preview
python -I -m fi.context remove --lock /path/to/project/.futureagi-context.lock.json \
  --plan /private/remove-plan.json
python -I -m fi.context recover --project /path/to/project --quiescent
```

- Omit the selector for production; a missing label is an error. Exact-version
  installation works before first promotion when the credential grants it.
- Both `codex` and `claude-code` profiles remain **preview**. Installation requires
  `--allow-preview`; adopting existing local instructions also requires
  `--adopt-local`. No settings, hooks, tool grants or plugins are implicitly enabled.
- Stop clients and other writers before apply/recover and acknowledge with
  `--quiescent`. POSIX-only writes use private journals/backups, preimage checks,
  cooperative locking and lock-last commit. Multiple paths are recoverable, not
  globally atomic for arbitrary live readers. An interrupted install requires
  reconciliation before another operation.
- Plans contain exact source/local bytes and a bounded resolution lease; keep them
  private. Apply rechecks the original immutable manifest with the same lease.
  Expiry/revocation/quarantine fails closed; explicitly replan rather than renewing
  part of a staged snapshot. Exact restore requires an eligible exact-version grant.
- Removal preserves modified/unowned files and reports them. Empty directories may
  remain. It does not revoke registry credentials or erase prior offline copies.
  `verify` checks bytes, not current remote authorization, native discovery, model
  delivery or behavior. `doctor` reports local diagnostics, not certification.
- JSON output has schema 1. Exit codes: 0 complete, 2 input/configuration syntax,
  3 denied/missing credentials, 4 transport, 5 stale/local filesystem conflict,
  6 integrity, 7 unsupported/unverified profile, 8 update available (`--check`).

Standalone skills use the same environment and journaled materializer, retaining the
cumulative v1 `.futureagi-skills.lock.json` plus a separate scoped ownership receipt:

```sh
python -I -m fi.skills plan --name refund --version 1 --client codex \
  --project /path/to/project --plan /private/skill-plan.json --allow-preview
python -I -m fi.skills inspect --plan /private/skill-plan.json
python -I -m fi.skills apply --plan /private/skill-plan.json --quiescent
python -I -m fi.skills verify --project /path/to/project
python -I -m fi.skills update --project /path/to/project --name refund --check
python -I -m fi.skills update --project /path/to/project --name refund \
  --plan /private/skill-update.json --allow-preview
python -I -m fi.skills restore --project /path/to/project --name refund \
  --lock /private/retained-skills.lock.json --plan /private/skill-restore.json --allow-preview
python -I -m fi.skills remove --project /path/to/project --name refund --plan /private/skill-remove.json
python -I -m fi.skills recover --project /path/to/project --quiescent
```

Restore requires current scoped ownership and verifies the retained version ID/digest;
updates preserve pins and refuse same-name identity replacement. Each invocation plans
one skill without erasing other installed entries. Tag-wide/batch install and reviewed
push remain unavailable. Context helpers live in `fi.context.materialize`; standalone
helpers live in `fi.skills.installer`; both share `fi.context.journal`.

### Optional backend and qualification gates

On Python 3.11, the `context-deepagents` extra installs exactly `deepagents==0.4.11`.
Other interpreters retain transport/CLI support without this optional runtime.
`fi.context.adapters.deepagents.mount_context(snapshot, default=..., authorize=...)`
uses the real read-only `/fi_context/` composite mount and preserves the
application's writable backend. Supply live authorization for each read. This is
backend protocol support only: session/checkpoint identity, clean-thread upgrades,
model-boundary delivery receipts and the Simulation entrypoint remain unimplemented
until their actual joint backend/application contract is frozen.

`ci.yml` targets the `self-hosted`, `linux`, `x64`, `context-sdk-gcp` runner pool
and checks the GCP metadata project before executing repository checks. Provisioning
this pool is an **unfulfilled operator prerequisite**, not a runner created by this
branch. Use disposable single-job, labelled, auto-deleting Ubuntu 24.04 VMs in
`fagi-omega-staging`; do not attach persistent credentials or trusted workloads to
PR runners. Missing runners leave the required gate incomplete; there is no hosted
or local fallback. The existing separate backend `e2e.yml` workflow still needs its
own approved GCP/E2B topology before execution. This branch does not register
runners, change credentials or enable paid/native qualification.

CI requires a separate Python 3.11 backend-conformance job, even though the base
interpreter matrix does not collect that optional suite. Installed-wheel gates run
snapshot/materializer regressions, the CLI transport integration probe and the
actual byte-verification action with corruption, pin and hostile-project controls.
The npm consumer gate checks declarations plus ESM/CommonJS public subpath exports.
The action installs nothing and executes no project code; it requires a preinstalled
trusted interpreter, exact SDK version and materializer hash. It is not behavioral CI.

Release prerequisites remain live integrated-backend credential conformance,
approved GCP/E2B native qualification orchestration, actual
host discovery/delivery qualification, full customer journeys, and normal reviewed
package publication. Native diagnostics and external application work require
separate approved jobs; ordinary unit-green cannot enable a profile. No 10x result
or native-session certification is established by these package gates.

## Adding your own methods (the hand-written layer)

The generator never owns the whole client. Four places are yours:

1. **A method on a resource.** `python/fi/platform/resources/datasets.py` (and `typescript/.../resources/datasets.ts`) is scaffolded once with `class Datasets(DatasetsResource)` and never overwritten. Add methods there; they compose generated ones or call an endpoint the catalog lacks through `self._t.raw(...)`. `resources/spans.py` is a real example: `client.spans.ingest(spans)` posts a JSON *array*, which the catalog cannot express.

   ```python
   class Datasets(DatasetsResource):
       def get_by_name(self, name: str) -> models.DatasetTableResult:
           match = next(d for d in self.list_names().datasets if d.name == name)
           return self.get(match.dataset_id)
   ```

2. **Swap a resource class.** `Client._resources` maps attribute → class, and every generated resource keeps its nested resources in `_children`:

   ```python
   class MyDatasets(Datasets):
       _children = {**DatasetsResource._children, "columns": MyColumns}

   class MyClient(Client):
       _resources = {**Client._resources, "datasets": MyDatasets, "billing": Billing}
   ```

   TypeScript: `new Client({ resources: { datasets: MyDatasets } })`; nested ones are reassigned in the subclass constructor.

3. **Any endpoint, with the same plumbing.** `client.request("DELETE", "/model-hub/prompt-labels/{id}/")` (auth, retries, envelope unwrap, typed errors; `multipart=True` and `files=` for uploads; `decode="text"` or `"auto"` for a body that is not JSON).

4. **Per call.** Every generated method takes `extra_query=` / `extra_body=` for fields the contract does not describe yet, and `options=RequestOptions(headers=..., timeout=..., max_retries=...)`. TypeScript: the last `options` argument carries `headers`, `timeout`, `maxRetries`, `extraQuery`, `extraBody`.

Prefer the catalog when the contract describes the endpoint; hand-write only what it cannot express (array bodies, compositions, streaming). A generated method may not take the name of a hand-written client attribute (`request`): the generator fails instead.

## The catalog (`catalog/operations.yaml`)

```yaml
- id: datasets.rows.add                       # -> client.datasets.rows.add() / MCP datasets_rows_add
  operation: {method: POST, path: "/model-hub/develops/{dataset_id}/add_rows/"}
  surfaces:
    sdk: {stability: beta}                    # SDK beta first (emits fi.platform.BetaWarning)
    mcp: false                                # not in MCP yet
```

Examples (the full list is the catalog):

| Catalog id | Python | TypeScript | MCP tool |
|---|---|---|---|
| `datasets.list` | `client.datasets.list()` (auto-paginated) | `client.datasets.list()` | `list_datasets` |
| `datasets.rows.add` | `client.datasets.rows.add()` (SDK beta) | `client.datasets.rows.add()` | `add_dataset_rows` (stable) |
| `datasets.create_from_file` | `client.datasets.create_from_file(file=...)` | `client.datasets.createFromFile({ file })` | not shipped (SDK-only) |
| `traces.list` | `client.traces.list()` | `client.traces.list()` | `search_traces` |
| `annotation_queues.items.submit` | `client.annotation_queues.items.submit()` | `client.annotationQueues.items.submit()` | `submit_annotation` |

The generator **fails** on any of these catalog mistakes: an unknown surface; an MCP entry without `group`/`access`; an operation missing from the contract; path placeholders that don't match the path params; a pagination param the endpoint doesn't have; a duplicate MCP tool name; body params on a paginated call; file params without `multipart`; a method name that shadows the hand-written client.

## Commands

```bash
pip install -e ./python pytest pyyaml

python sdkgen/sync_contract.py ../future-agi/api_contracts/openapi/swagger.json   # refresh the contract slice
python sdkgen/generate.py                            # regenerate everything, scaffold new resources
python sdkgen/generate.py --only python              # one or both of: python, typescript
python sdkgen/generate.py --check                    # CI: exit 1 if generated code is stale or a scaffold is missing

# Live tests against a real backend, e.g. a local install of the monorepo (./bin/install)
python sdkgen/local_api_key.py --email <admin email> --password-file <file>       # writes .env.local (gitignored)
python sdkgen/local_api_key.py --signup --base-url http://localhost:8100           # or: a fresh account on a throwaway stack
pytest python/tests/platform -v                      # Python: every catalog operation
cd typescript/futureagi && pnpm install && pnpm test:live   # TypeScript: transport, uploads, pagination, errors, hand-written method
```

Without `.env.local` or `FI_*` env vars, the live tests are skipped and only the generator and transport tests run. With `FI_E2E_REQUIRED=1` (CI) they fail instead.

`sdkgen/generator/` is one module per concern: `catalog.py` loads and validates (every emitter starts from its `Op` list), `python.py` and `typescript.py` only emit text, and `__init__.py` maps outputs to paths. Adding a surface is a new emitter plus one entry in `build()`.

## Responses that don't match the contract

Live testing showed the contract is often wrong about responses. The SDK handles this in three layers:

- **The transport** unwraps the backend's `{status, result}` envelope whenever it is present, because the contract leaves it out on many operations.
- **The generator** loosens patterns drf-yasg always gets wrong. Every `SerializerMethodField` comes out as a read-only `string`, and untyped `ListField`s come out as lists of strings; both are typed `Any` / `unknown`. Free-form `object` fields are `Any`. Output list items may be null. Numbers are accepted where the contract says string.
- **The generator** also makes every PATCH body partial (the backend accepts any subset of the fields; drf-yasg documents the create serializer's required fields), types `x-json-value` inputs as any JSON value (`Any` / `JsonValue`: a string or number as much as an object), and lists each response model's contract-required fields in `__required__` for strict mode.
- **`contract_fix`** in the catalog corrects one operation, with a `note` naming the backend bug; the generation target stays the selected surface, and the fix is the narrowest that makes it right. Response-side options: `returns: Definition` (the response is really another definition of the contract, e.g. a create that answers with the detail serializer), `returns: {field: type}` (an object the contract has no definition for; one named `<Resource><Method>Result` is generated), `optional_in_response: [field]` (a write-only input the serializer also documents as a required output), `page_items` (an "array" that is really a page object) and `untyped` (the schema is simply wrong). Request-side options: `body_fields: {field: type}` patches single fields and keeps the rest of the contract's body, so a field the backend adds later still reaches the SDK; `body: {field: type}` replaces the whole body, only for a contract that documents the wrong serializer altogether (drf-yasg often shows the *response* serializer as the request body); `body_required: [...]` overrides which fields are required (e.g. a PATCH that is not partial); `query: {field: type}` adds filters the contract leaves out. Types are `string | integer | number | boolean | object | array | file | json`, or `X[]` for a list; a value may be `{type: T, as: argument_name}` when the wire name makes a poor argument. **Every fix is checked against the contract:** once the backend has fixed its contract, a fix that no longer changes anything (`body` equal to the contract's body, a `query` field the contract has, a `returns` the contract already states, ...) fails the build, so it gets removed instead of becoming a second permanent contract.
- **`operation.multipart: true`** sends body fields as form data and `file`-typed params as uploads (`client.file_knowledge_bases.create(name=..., files=[path, ("a.txt", b"...")])`). A file argument is a path, bytes, an open binary file, or a `(filename, bytes)` pair; in TypeScript a path, `Uint8Array`, `Blob`, or `{ name, data }`.
- **`operation.decode: text | auto`** for a response that is not JSON: `text` returns the body as a string, `auto` does so unless the response says it is JSON (`annotation_queues.export`, which returns CSV for `export_format=csv`). The method's return type becomes `str` / `Any` (`string` / `unknown`).

By default, a Python response that still doesn't match gives you the raw JSON and a `ResponseShapeWarning`, so a backend change never breaks a user's call; a field the response leaves out is simply `None`. `Client(strict_responses=True)` separates tolerant parsing from contract validation: a response missing a field the contract marks required (and not nullable) raises `ResponseValidationError`, as does one that does not parse. The live tests run strict, so a backend that stops sending a required field fails them. The TypeScript client types responses at compile time only and returns the JSON as is.

**The packages as installed.** `python/consumer/consumer.py` and `typescript/futureagi/consumer/consumer-types.mts` hold the public calls that must work from a user's project: CI builds the wheel and the npm tarball, installs each into an empty environment and runs / type-checks the consumer there (`mypy --strict`; `tsc --strict` against the published `.d.ts`, `typescript/futureagi/scripts/check-consumer.sh`). An internal build can pass while a public call does not type-check; that is what these catch.

## Found while testing against a real backend

- **Pages start at 0:** `get-datasets` treats `page=0` as the first page, which the contract doesn't say (`first_page: 0`).
- **Wrong error codes:** an unknown dataset, prompt or dashboard returns **400**, not 404. An unknown simulation execution returns **500**.
- **Wrong response shapes:** fixed with `contract_fix`, each one a backend contract bug to fix at the source.
  - `agents.list` and `simulation.executions.list` return DRF pages, not bare arrays.
  - `projects.list` and `evals.groups.list` return `{projects|data, total_count}`, not DRF pages.
  - `optimizations.list` returns `{metadata, table}`.
  - `prompts.versions.list` returns a page of versions, not one template.
  - `gateway.analytics` returns overview stats, not request logs.
  - `gateway.guardrail_rules.list` returns `{rules}`.
  - `gateway.sessions.requests` returns a list of request logs, not a session.
- **Wrong request bodies:** `prompt-templates/create-draft`, `{id}/commit`, `{id}/add-new-draft`, `generate-prompt`, `improve-prompt` and every `prompt-labels/*` action document the response serializer as the request body (`contract_fix.body`); `scores` POST documents the JSON `value` as an object (`body_fields: {value: json}`); `eval-task/update_eval_task/` is a PATCH that does need `eval_task_id` and `edit_type` (`body_required`). PATCH bodies marked required (`dashboard/{id}`, `annotation-queues/{id}`) need no fix: the generator makes every PATCH partial.
- **Wrong response definitions:** `dashboard` POST/PATCH answer with the detail serializer, not the create one (`returns: DashboardDetail`); `prompt-templates/{id}/run_template/` answers with an execution receipt (`template_id`, `prompt_config`, ...) that the contract documents as the request (`returns: {...}`); `custom-eval-config` POST answers with the id only; `dataset-optimization` POST drops the `column_id` it documents as required; `annotation-queues` responses never carry the write-only `label_ids` the serializer marks required (`optional_in_response`).
- **Missing query params:** `prompt-history-executions` (`template_id`), `prompt-labels/get-by-name` (`name`, `label`, `version`) and `prompt-labels/template-labels` (`template_id`, `template_name`) are documented with paging params only.
- **Multipart uploads documented as JSON:** `create-dataset-from-local-file` and `knowledge-base` POST/PATCH take `multipart/form-data` with a repeated `file` field; the contract shows a JSON body with a string `file`. A missing `model_type` on the dataset upload returns **500**, not 400.
- **Knowledge-base worker races:** a `knowledge-base` PATCH that adds files is refused (**400** "Unable to update") while an earlier upload is still being processed, yet the refused request stores its file anyway; and a file being processed is silently not deleted. Both tests wait for the worker before updating or deleting.
- **Two knowledge-base stores:** `/model-hub/kb/` (a `KnowledgeBase` with an embedding model and a chunk size; MCP's list/get) and `/model-hub/knowledge-base/` (the app's Knowledge Base page: a `KnowledgeBaseFile` collection of uploaded documents, the API the old `fi.kb` module used) are separate models, so an id from one is a 404 on the other. The SDK exposes them as two resources, each with a coherent lifecycle: `knowledge_bases` (list, get, create, update, delete) and `file_knowledge_bases` (create with uploads, update, list, list_names, delete, `.files.list`, `.files.delete`).
- **`annotations-labels` list** returns a DRF page, not an array; **`prompt-templates/{id}/commit`** returns a message string, not the template.
- **Eval tasks start `pending`:** a background worker moves them to `running`, and only a running task can be paused; the test waits for it.
- **Span ingestion race:** posting several spans for a new project in one call can fail on `unique_project_per_org_type`, because the server creates the project from parallel threads.
- **Wrong request body type:** `create_otel_span` takes a JSON array, but the contract says object (hence the hand-written `client.spans.ingest`).

## Test coverage

`python/tests/platform/test_all_operations_live.py` calls **every** catalog operation against a live backend. Its last test fails if any operation was never called, and prints what each one returned.

Against a local `bin/install` backend:
- **145 of 158** operations succeed, and their responses validate strictly.
- **13** return the backend's typed error: plan-gated features (`402`); `usage.overview`, which self-hosted installs don't serve (`404`); trace, span and session reads, which wait on ClickHouse indexing; simulation runs, which wait on scenario generation; `evals.test`, which needs a model provider; `datasets.create_from_huggingface`, which needs outbound access to huggingface.co; lookups of ids that don't exist on a fresh install.

`typescript/futureagi/src/platform/__tests__/` covers the TypeScript transport and generated code against an injected `fetch` (bodies, encoding, every pagination style, retries, errors, uploads, per-call options, resource overrides) and, with `pnpm test:live`, the same flows against the backend: datasets, uploads, prompts with drafts and labels, the hand-written `spans.ingest`, annotation labels and queues, knowledge bases, typed errors.

`python/tests/platform/test_generator.py` fails if any generated file (Python or TypeScript) is stale or a resource scaffold is missing.

## CI

Two workflows in this repository, both on every pull request and on pushes to `dev` and `main`:

- `.github/workflows/ci.yml`: `generate.py --check`, `check_mcp_parity.py` (the catalog's MCP names against the monorepo's tool list at the backend release in `sdkgen/contracts/BACKEND_VERSION`: a sync that brings new tools fails until the catalog has their entries), ruff on the generator and platform/context/skills modules and tests, the base Python unit suite on 3.9, 3.11 and 3.13, required pinned Deep Agents backend conformance on 3.11, installed wheel/action and npm consumers, and TypeScript type checking, platform/snapshot tests and builds. Requires the disposable GCP runner pool described above. Gate: `CI Pass`.
- `.github/workflows/e2e.yml`: the live suites against a real backend. It boots the Standalone setup the way the monorepo's E2E CI does (its `docker-compose.yml` plus `e2e/stack/docker-compose.standalone-e2e.yml`, the released `futureagi/standalone:latest` image, the mock LLM), signs up a fresh account with `local_api_key.py --signup`, and runs `python/tests/platform` on 3.9 and 3.12 and `pnpm test:live`. Also nightly, and on demand with another image tag. Gate: `E2E Tests Pass`.

The monorepo's E2E CI (`future-agi/.github/workflows/e2e-ci.yml`, PRs and pushes on `dev` and `main`) runs the same two live suites against every backend build, so a backend change that breaks the SDK fails there before it is released. It checks out this repository at the branch named like the monorepo PR's branch if one exists, else the base branch (`dev` or `main`).

## Release cycle

**Main is the release boundary.** Backend syncs still open SDK updates on `dev`, but a dev push never authorizes publication.

1. `promote.yml` prepares the `dev → main` PR for human review and never auto-merges it. Preserve Conventional Commit history with a merge commit.
2. After both main-push CI and E2E succeed, `release-please.yml` prepares the version/changelog PR. A fail-closed guard approves only the release app's validated version-only diff, and normal required checks control its auto-merge.
3. After that version commit passes main-push CI/E2E, release-please creates package tags and dispatches `publish.yml` on main.
4. Publication requires a real tag on main and passing checks for its exact commit. PyPI and npm use OIDC trusted publishing, not persistent registry tokens. Published packages are reinstalled and smoke-tested.

See [RELEASING.md](RELEASING.md) for the exact app, registry, environment, approval, and recovery configuration. These workflows do not bypass reviews on ordinary code or promotion PRs.

Not gated in CI: the repository's `.pre-commit-config.yaml` (black, flake8, isort) and `eslint`. Running them on the whole repository today reports 70 files isort would reorder and no ESLint config, so enforcing them needs a cleanup commit first; ruff (E, F, W, I) on the generator and the platform client runs in `ci.yml` meanwhile.

The one-time setup is required before automatic releases work. Missing app credentials or registry trust fail loudly; they do not silently publish or bypass checks. The [release runbook](RELEASING.md#one-time-setup) is the canonical setup checklist.

- Run `generate.py --check`, `pytest python/tests/platform` and `pnpm test` in CI against a backend started from the monorepo.
- Move `operations.yaml` into the monorepo next to the MCP catalog (`tools.yaml`), so one file drives MCP and the SDKs and the sync workflow copies it here with the contract.
- Deprecate the hand-written modules (`fi.datasets`, `fi.prompt`, `fi.kb`, `fi.queues`, `fi.annotations`, and their TypeScript counterparts) in favour of the generated client, then remove them in a major release.
