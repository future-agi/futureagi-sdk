# sdkgen: SDK + MCP from one contract and one catalog

`sdkgen` generates `fi.platform`, the one-client SDK (`from fi import Client`), from the backend's API contract plus a small catalog. The same catalog also produces the MCP tool list, so an operation has the same name in both, and each operation can still ship to just one of them.

It covers **all 105 MCP tools** (imported from the monorepo's `futureagi/mcp_server/catalog/tools.yaml`, keeping every MCP tool name), plus **53 SDK-only operations** that give `fi.Client` everything the hand-written `fi.datasets`, `fi.prompt`, `fi.kb`, `fi.queues` and `fi.annotations` modules can do: 158 operations across 24 resources. The MCP manifest still has exactly 105 tools.

```
future-agi/api_contracts/openapi/swagger.json ──sync_contract.py──▶ sdkgen/contracts/swagger.json
                                                                    sdkgen/catalog/operations.yaml
                                                                            │
                                                                    sdkgen/generate.py
                                                  ┌─────────────────────────┴─────────────────────────┐
                              python/fi/platform/_generated/{models,resources}.py        sdkgen/mcp/tools.generated.json
                                                  │
                    hand-written core: python/fi/platform/{_client,_transport,_pagination,_errors}.py
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

- **Shared config:** keys and base URL are set once on the client.
- **Async:** `AsyncClient` has the same methods (`await`, `async for`).
- **Envelope removed:** the backend's `{status, result}` wrapper is unwrapped before you get the result.
- **Typed errors:** `fi.platform.BadRequestError`, `NotFoundError`, `AuthenticationError`, ..., carrying the backend's `type`, `code` and `detail`.
- **Retries:** 429 is retried for every call. Timeouts, 5xx and dropped connections are retried only for calls that are safe to repeat (GET, PUT, DELETE), so a POST the server already applied is never sent twice.
- **Your own `httpx` client:** `Client(http_client=...)` uses it as given and never closes it.
- **One error family:** every error derives from `fi.utils.errors.SDKException`, like the existing modules.
- **Old code still works:** the existing modules (`fi.datasets.Dataset`, `fi.queues`, ...) are untouched and keep working.

`client.<resource>`: `account`, `workspaces`, `datasets` (`.columns`, `.rows`, `.cells`, `.evals`, `.prompts`), `knowledge_bases`, `prompts` (`.versions`), `evals` (`.templates`, `.groups`, `.tasks`, `.configs`), `projects`, `traces` (`.properties`), `spans`, `sessions`, `alerts` (`.logs`, `.rules`), `error_clusters`, `annotation_queues` (`.items`), `experiments`, `optimizations`, `agents` (`.versions`), `simulation` (`.scenarios`, `.tests`, `.executions`), `gateway` (`.request_logs`, `.guardrail_rules`, `.sessions`), `dashboards` (`.widgets`, `.metrics`), `usage`.

Every method also takes `extra_query=` / `extra_body=` for fields the contract does not describe yet. See `python/examples/platform_client.py` for a runnable tour.

## The catalog (`catalog/operations.yaml`)

```yaml
- id: datasets.rows.add                       # -> client.datasets.rows.add() / MCP datasets_rows_add
  operation: {method: POST, path: "/model-hub/develops/{dataset_id}/add_rows/"}
  surfaces:
    sdk: {stability: beta}                    # SDK beta first (emits fi.platform.BetaWarning)
    mcp: false                                # not in MCP yet
```

Examples (the full list is the catalog):

| Catalog id | SDK | MCP tool |
|---|---|---|
| `datasets.list` | `client.datasets.list()` (auto-paginated) | `list_datasets` |
| `datasets.rows.add` | `client.datasets.rows.add()` (SDK beta) | `add_dataset_rows` (stable) |
| `datasets.columns.add` | `client.datasets.columns.add()` | not shipped (SDK-only) |
| `traces.list` | `client.traces.list()` | `search_traces` |
| `annotation_queues.items.submit` | `client.annotation_queues.items.submit()` | `submit_annotation` |
| `gateway.analytics` | `client.gateway.analytics()` | `get_gateway_analytics` |

The generator **fails** on any of these catalog mistakes:
- an unknown surface;
- an MCP entry without `group`/`access`;
- an operation missing from the contract;
- path placeholders that don't match the path params;
- a pagination param the endpoint doesn't have;
- a duplicate MCP tool name.

## Commands

```bash
pip install -e ./python pytest pyyaml

python sdkgen/sync_contract.py ../future-agi/api_contracts/openapi/swagger.json   # refresh the contract slice
python sdkgen/generate.py                                                         # regenerate
python sdkgen/generate.py --check                                                 # CI: exit 1 if generated code is stale

# Live tests against a real backend, e.g. a local install of the monorepo (./bin/install)
python sdkgen/local_api_key.py --email <admin email> --password-file <file>       # writes .env.local (gitignored)
pytest python/tests/platform -v
```

Without `.env.local` or `FI_*` env vars, the live tests are skipped and only the generator tests run.

## Responses that don't match the contract

Live testing showed the contract is often wrong about responses. The SDK handles this in three layers:

- **The transport** unwraps the backend's `{status, result}` envelope whenever it is present, because the contract leaves it out on many operations.
- **The generator** loosens patterns drf-yasg always gets wrong. Every `SerializerMethodField` comes out as a read-only `string`, and untyped `ListField`s come out as lists of strings; both are typed `Any`. Free-form `object` fields are `Any`. Output list items may be null. Numbers are accepted where the contract says string.
- **`contract_fix`** in the catalog corrects one operation, with a `note` naming the backend bug. Response-side options: `page_items` (an "array" that is really a page object) and `untyped` (the schema is simply wrong). Request-side options, for the many endpoints where drf-yasg documents the *response* serializer as the request body: `body: {field: type}` replaces the body fields, `body_required: [...]` overrides which are required (a PATCH is partial), and `query: {field: type}` adds filters the contract leaves out. Types are `string | integer | number | boolean | object | array | file`, or `X[]` for a list; a body value may be `{type: T, as: python_name}` when the wire name makes a poor argument.
- **`operation.multipart: true`** sends body fields as form data and `file`-typed params as uploads (`client.knowledge_bases.create(name=..., files=[path, ("a.txt", b"...")])`). A file argument is a path, bytes, an open binary file, or a `(filename, bytes)` pair.

By default, a response that still doesn't match gives you the raw JSON and a `ResponseShapeWarning`, so a backend change never breaks a user's call. `Client(strict_responses=True)` raises `ResponseValidationError` instead; the tests run strict.

## Found while testing against a real backend

- **Pages start at 0:** `get-datasets` treats `page=0` as the first page, which the contract doesn't say (`first_page: 0`).
- **Wrong error codes:** an unknown dataset returns **400**, not 404, and so does a deleted dashboard. An unknown simulation execution returns **500**.
- **Wrong response shapes:** these are fixed with `contract_fix`, and each one is a backend contract bug to fix at the source.
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
- **Two knowledge-base stores:** `/model-hub/kb/` (used by MCP's list/get) does not see knowledge bases created through `/model-hub/knowledge-base/` (the upload API the SDK has always used), and `get` on one returns 404.
- **`annotations-labels` list** returns a DRF page, not an array; **`prompt-templates/{id}/commit`** returns a message string, not the template.
- **Span ingestion race:** posting several spans for a new project in one call can fail on `unique_project_per_org_type`, because the server creates the project from parallel threads.
- **Wrong request body type:** `create_otel_span` takes a JSON array, but the contract says object.

## Test coverage

`python/tests/platform/test_all_operations_live.py` calls **every** catalog operation against a live backend. Its last test fails if any operation was never called, and prints what each one returned.

Against a local `bin/install` backend:
- **145 of 158** operations succeed, and their responses validate strictly.
- **13** return the backend's typed error:
  - plan-gated features (`402`);
  - `usage.overview`, which self-hosted installs don't serve (`404`);
  - trace, span and session reads, which wait on ClickHouse indexing;
  - simulation runs, which wait on scenario generation;
  - `evals.test`, which needs a model provider;
  - `datasets.create_from_huggingface`, which needs outbound access to huggingface.co;
  - lookups of ids that don't exist on a fresh install.

## Next steps

- Add the endpoints MCP doesn't have yet (delete for prompts, queues and projects; prompt commit; annotation labels) as SDK-only entries.
- Run `generate.py --check` and the live tests in CI against a backend started from the monorepo.
- Move `operations.yaml` into the monorepo next to the MCP catalog, so `tool_generation.py` reads the MCP entries from it.
