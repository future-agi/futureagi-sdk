# sdkgen: SDK + MCP from one contract and one catalog

`sdkgen` generates `fi.platform`, the one-client SDK (`from fi import Client`), from the backend's API contract plus a small catalog. The same catalog also produces the MCP tool list, so an operation has the same name in both, and each operation can still ship to just one of them.

This first cut covers **datasets** only. Other resources are added the same way.

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
- **Retries:** automatic retries on 408, 429 and 5xx.
- **Old code still works:** the existing modules (`fi.datasets.Dataset`, `fi.queues`, ...) are untouched and keep working.

## The catalog (`catalog/operations.yaml`)

```yaml
- id: datasets.rows.add                       # -> client.datasets.rows.add() / MCP datasets_rows_add
  operation: {method: POST, path: "/model-hub/develops/{dataset_id}/add_rows/"}
  surfaces:
    sdk: {stability: beta}                    # SDK beta first (emits fi.platform.BetaWarning)
    mcp: false                                # not in MCP yet
```

| Catalog id | SDK | MCP tool |
|---|---|---|
| `datasets.list` | `client.datasets.list()` | `list_datasets` (keeps today's name) |
| `datasets.create` | `client.datasets.create()` | `create_dataset` |
| `datasets.get` | `client.datasets.get()` | `get_dataset` |
| `datasets.columns.add` | `client.datasets.columns.add()` | `datasets_columns_add` |
| `datasets.rows.add` | `client.datasets.rows.add()` (beta) | not shipped yet |
| `datasets.delete` | `client.datasets.delete()` | not shipped (destructive) |

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

## Found while testing against a real backend

- **Pages start at 0:** `GET /model-hub/develops/get-datasets/` treats `page=0` as the first page. The contract doesn't say this. The catalog records it (`first_page: 0`).
- **Unknown dataset gives 400:** `GET /model-hub/develops/{id}/get-dataset-table/` returns **400** `validation_error`, not 404.

## Next steps

- Add the next resources (prompts, annotation queues, tracing, gateway management) as catalog entries.
- Run `generate.py --check` and the live tests in CI against a backend started from the monorepo.
- Move `operations.yaml` into the monorepo next to the MCP catalog, so `tool_generation.py` reads the MCP entries from it.
