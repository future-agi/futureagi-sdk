# sdkgen: Python SDK and TypeScript SDK from one contract and one catalog

`sdkgen` generates the platform client for both SDKs (`fi.Client` in Python, `new Client()` in TypeScript) from the backend's API contract plus a small catalog. The catalog records, for each operation, the MCP tool it corresponds to in the monorepo (`futureagi/mcp_server/catalog/tools.yaml`), so an operation has the same name in the SDKs and in MCP; the MCP server itself is generated and served from the monorepo, not here.

It covers the operations behind **all 105 MCP tools** (same names) plus **53 SDK-only operations** that give the clients everything the hand-written `fi.datasets`, `fi.prompt`, `fi.kb`, `fi.queues` and `fi.annotations` modules can do: 158 operations across 24 resources. The monorepo's E2E CI checks that the catalog's MCP names still match the monorepo's tool list.

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
await client.knowledgeBases.create({ name: "docs", file: ["./notes.txt", { name: "a.txt", data: "..." }] });
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

`client.<resource>`: `account`, `workspaces`, `datasets` (`.columns`, `.rows`, `.cells`, `.evals`, `.prompts`), `knowledge_bases` (`.files`), `prompts` (`.versions`, `.labels`), `evals` (`.templates`, `.groups`, `.tasks`, `.configs`), `projects`, `traces` (`.properties`), `spans`, `sessions`, `alerts` (`.logs`, `.rules`), `error_clusters`, `annotations` (`.labels`), `annotation_queues` (`.items`), `scores`, `experiments`, `optimizations`, `agents` (`.versions`), `simulation` (`.scenarios`, `.tests`, `.executions`), `gateway` (`.request_logs`, `.guardrail_rules`, `.sessions`), `dashboards` (`.widgets`, `.metrics`), `models`, `provider_keys`, `usage`.

See `python/examples/platform_client.py` for a runnable tour.

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
- **`contract_fix`** in the catalog corrects one operation, with a `note` naming the backend bug. Response-side options: `page_items` (an "array" that is really a page object) and `untyped` (the schema is simply wrong). Request-side options, for the many endpoints where drf-yasg documents the *response* serializer as the request body: `body: {field: type}` replaces the body fields, `body_required: [...]` overrides which are required (a PATCH is partial), and `query: {field: type}` adds filters the contract leaves out. Types are `string | integer | number | boolean | object | array | file`, or `X[]` for a list; a body value may be `{type: T, as: argument_name}` when the wire name makes a poor argument.
- **`operation.multipart: true`** sends body fields as form data and `file`-typed params as uploads (`client.knowledge_bases.create(name=..., files=[path, ("a.txt", b"...")])`). A file argument is a path, bytes, an open binary file, or a `(filename, bytes)` pair; in TypeScript a path, `Uint8Array`, `Blob`, or `{ name, data }`.
- **`operation.decode: text | auto`** for a response that is not JSON: `text` returns the body as a string, `auto` does so unless the response says it is JSON (`annotation_queues.export`, which returns CSV for `export_format=csv`). The method's return type becomes `str` / `Any` (`string` / `unknown`).

By default, a Python response that still doesn't match gives you the raw JSON and a `ResponseShapeWarning`, so a backend change never breaks a user's call. `Client(strict_responses=True)` raises `ResponseValidationError` instead; the tests run strict. The TypeScript client types responses at compile time only and returns the JSON as is.

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
- **Wrong request bodies:** `prompt-templates/create-draft`, `{id}/commit`, `{id}/add-new-draft`, `generate-prompt`, `improve-prompt` and every `prompt-labels/*` action document the response serializer as the request body; `annotation-queues/{id}` PATCH marks `name` and `label_ids` required. Fixed with `contract_fix.body` / `body_required`.
- **Missing query params:** `prompt-history-executions` (`template_id`), `prompt-labels/get-by-name` (`name`, `label`, `version`) and `prompt-labels/template-labels` (`template_id`, `template_name`) are documented with paging params only.
- **Multipart uploads documented as JSON:** `create-dataset-from-local-file` and `knowledge-base` POST/PATCH take `multipart/form-data` with a repeated `file` field; the contract shows a JSON body with a string `file`. A missing `model_type` on the dataset upload returns **500**, not 400.
- **Knowledge-base worker races:** a `knowledge-base` PATCH that adds files is refused (**400** "Unable to update") while an earlier upload is still being processed, yet the refused request stores its file anyway; and a file being processed is silently not deleted. Both tests wait for the worker before updating or deleting.
- **Two knowledge-base stores:** `/model-hub/kb/` (used by MCP's list/get) does not see knowledge bases created through `/model-hub/knowledge-base/` (the upload API the SDK has always used), and `get` on one returns 404.
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

- `.github/workflows/ci.yml`: `generate.py --check`, `check_mcp_parity.py` (the catalog's MCP names against the monorepo's tool list at the backend release in `sdkgen/contracts/BACKEND_VERSION`: a sync that brings new tools fails until the catalog has their entries), ruff on the generator and the platform client, the Python unit suite on 3.9, 3.11 and 3.13, and the TypeScript type check, platform tests and build. Gate: `CI Pass`.
- `.github/workflows/e2e.yml`: the live suites against a real backend. It boots the Standalone setup the way the monorepo's E2E CI does (its `docker-compose.yml` plus `e2e/stack/docker-compose.standalone-e2e.yml`, the released `futureagi/standalone:latest` image, the mock LLM), signs up a fresh account with `local_api_key.py --signup`, and runs `python/tests/platform` on 3.9 and 3.12 and `pnpm test:live`. Also nightly, and on demand with another image tag. Gate: `E2E Tests Pass`.

The monorepo's E2E CI (`future-agi/.github/workflows/e2e-ci.yml`, PRs and pushes on `dev` and `main`) runs the same two live suites against every backend build, so a backend change that breaks the SDK fails there before it is released. It checks out this repository at the branch named like the monorepo PR's branch if one exists, else the base branch (`dev` or `main`).

## Release cycle

A backend release becomes an SDK release on its own:

1. **Backend release** (`vX.Y.Z` tag in the monorepo, images published by `release-images`) triggers the monorepo's `sdk-sync` workflow. It runs `sync_contract.py --backend-version vX.Y.Z` and `generate.py` against that tag's `swagger.json` and opens a pull request here on `dev` (`feat(contract): sync with backend vX.Y.Z`, or `chore(contract): ...` when nothing generated changed). The PR's E2E run tests against `futureagi/standalone:vX.Y.Z`, the pin in `sdkgen/contracts/BACKEND_VERSION`, and the PR merges itself when `CI Pass` and `E2E Tests Pass` are green.
2. **`promote.yml`** keeps one `dev → main` pull request open (the SDK's release PR, merged with a merge commit as in the monorepo). It merges itself only while every commit on `dev` that `main` lacks is a sync commit; the moment anything else lands on `dev`, auto-merge is switched off and the PR waits for a person, so a feature awaiting review never rides a backend release to PyPI and npm.
3. **`release-please.yml`** on `main` opens the version PR from the conventional commits: `python/pyproject.toml` + `python/fi/__init__.py` and `typescript/futureagi/package.json`, with a changelog per package (`release-please-config.json`, `.release-please-manifest.json`). `feat` bumps the minor version, `fix` the patch. It merges itself once CI passes and creates the tags `python-vX.Y.Z` / `typescript-vX.Y.Z` and their GitHub releases.
4. **`publish.yml`** on a published release builds the package at that tag, checks the version matches the tag, and uploads: PyPI through trusted publishing (environment `pypi`), npm with `NPM_TOKEN` and provenance. Skips a version that is already there. Then it installs the published version from the index into a clean environment and runs a quickstart (import, build a client, every resource present, the transport's own error on a dead host; CommonJS and ESM for npm), so a release that installs broken fails loudly.
5. **`pr-title-lint.yml`** makes Conventional Commits titles a merge gate on `dev` and `main`: this repository squash-merges, so the title is the commit message release-please reads, and "updated stuff" would ship with no version bump and no changelog line.

Not gated in CI: the repository's `.pre-commit-config.yaml` (black, flake8, isort) and `eslint`. Running them on the whole repository today reports 70 files isort would reorder and no ESLint config, so enforcing them needs a cleanup commit first; ruff (E, F, W, I) on the generator and the platform client runs in `ci.yml` meanwhile.

One-time setup, repository admin: install the org's release bot app on this repository and expose `RELEASE_BOT_APP_ID` / `RELEASE_BOT_PRIVATE_KEY` (the monorepo's release-please secrets; pull requests opened with the default token get no CI runs); enable "Allow auto-merge"; require `CI Pass` and `E2E Tests Pass` on `dev` and `main`; register the trusted publisher on PyPI (`futureagi`, workflow `publish.yml`, environment `pypi`); add `NPM_TOKEN`. Without the app secrets the sync still opens its PR with a warning instead of auto-merging; without auto-merge every step above is the same, with a human clicking merge.

- Run `generate.py --check`, `pytest python/tests/platform` and `pnpm test` in CI against a backend started from the monorepo.
- Move `operations.yaml` into the monorepo next to the MCP catalog (`tools.yaml`), so one file drives MCP and the SDKs and the sync workflow copies it here with the contract.
- Deprecate the hand-written modules (`fi.datasets`, `fi.prompt`, `fi.kb`, `fi.queues`, `fi.annotations`, and their TypeScript counterparts) in favour of the generated client, then remove them in a major release.
