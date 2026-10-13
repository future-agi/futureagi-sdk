# OpenAPI Generated SDK Plan

## Goal

Generate low-level SDK clients from the backend OpenAPI contract, then expose a small handwritten wrapper that is stable and easy to consume.

## Shape

- `openapi/sdk/operation-aliases.json` patches backend `METHOD /path` entries into clean `operationId` values before generation.
- `openapi/sdk/wrapper-map.json` records the public wrapper namespace and the generated operation each method calls.
- `scripts/build-sdk-openapi.sh` converts the backend Swagger file to OpenAPI 3, filters public SDK paths, prunes unreachable schemas, and applies aliases.
- `scripts/generate-oss-sdk.sh` regenerates both generated clients:
  - TypeScript: `typescript/futureagi/src/generated/openapi`
  - Python: `python/fi/generated/openapi_client`
- `scripts/generate-go-java-sdk.sh` regenerates low-level generated clients:
  - Go: `go/futureagi`
  - Java: `java/futureagi`
- Handwritten wrappers live outside generated folders:
  - TypeScript: `FutureAGIClient` in `typescript/futureagi/src/futureagi-client.ts`
  - Python: `FutureAGIClient` in `python/fi/futureagi_client.py`
- The public generated spec currently covers the high-value management areas:
  - annotation queues and annotation labels
  - datasets and dataset table operations
  - experiments v2
  - simulation run tests, test executions, personas, scenarios, and agent definitions
  - tracing projects, traces, sessions, voice calls, annotations, and error feed issues
  - user/workspace member lookups
  - alert monitors, alert graphs, and alert logs

## Usage

TypeScript:

```ts
import { FutureAGIClient } from '@future-agi/sdk';

const client = new FutureAGIClient({ apiKey, secretKey });

const queues = await client.annotationQueues.list({ limit: 20 });
const item = await client.annotationQueues.items.next(queueId);
const datasets = await client.datasets.list({ page: 1 });
const experimentRows = await client.experiments.rows(experimentId);
const runTests = await client.simulations.runTests.list();
const traces = await client.tracing.traces({ project_id: projectId });
const me = await client.users.current();
const alertOptions = await client.alerts.metricOptions({ project_id: projectId });

await client.annotationQueues.discussion.comment(queueId, itemId, {
  comment: '@reviewer can you check the thumbs label?',
  mentioned_user_ids: [reviewerId],
});
```

Python:

```py
from fi import FutureAGIClient

client = FutureAGIClient(api_key=api_key, secret_key=secret_key)

queues = client.annotation_queues.list(limit=20)
item = client.annotation_queues.items.next(queue_id)
datasets = client.datasets.list(page=1)
experiment_rows = client.experiments.rows(experiment_id)
run_tests = client.simulations.run_tests.list()
traces = client.tracing.traces(project_id=project_id)
me = client.users.current()
alert_options = client.alerts.metric_options(project_id=project_id)

client.annotation_queues.discussion.comment(queue_id, item_id, {
    "comment": "@reviewer can you check the thumbs label?",
    "mentioned_user_ids": [reviewer_id],
})
```

## Regeneration

Run from the repository root:

```bash
scripts/generate-oss-sdk.sh
```

For Go and Java low-level clients:

```bash
scripts/generate-go-java-sdk.sh
```

When backend names are ugly or unstable, update `openapi/sdk/operation-aliases.json` first. When the public wrapper should expose a different name, update `openapi/sdk/wrapper-map.json` and the handwritten wrapper.

Generated files should not contain product-level ergonomics. Keep auth defaults, retries, examples, and naming choices in the handwritten wrapper.

## Dataset/experiment lifecycle slice

The six lifecycle methods are derived from core commit `17d864bf578ba361f450fc71019dc660f57c79e9` (PR #3475). `openapi/sdk/lifecycle-source.json` records the reviewed operations and source revision. The scoped build updates those operations and their component closure in the existing SDK spec; other SDK operations/components remain unchanged. `futureagi-sdk.operations.txt` lists the final public operation IDs after aliases (467 operations: 461 existing plus six new).

The default generator still refreshes the full public surface. To reproduce this additive slice, pass the explicit scope:

```bash
SDK_OPERATION_SCOPE="$PWD/openapi/sdk/lifecycle-source.json" \
  scripts/generate-oss-sdk.sh /path/to/core-at-17d864bf/api_contracts/openapi/swagger.json
```

Generation pins swagger2openapi 7.0.8, @hey-api/openapi-ts 0.97.3 with TypeScript 5.8.3, and openapi-python-client 0.28.4. Python post-hooks use isolated Ruff configuration targeting Python 3.10, preventing ambient user rules from rewriting TypeVars to Python 3.11-only `typing.Self`. The JSON conversion preserves scalar/list/object/null values, explicit non-null snapshot inputs, and nullable enums.

The trial-stability refresh is scoped to the existing comparison POST using core
PR #3483 (`32ea09fa63d0ffa2e5178d1ede94f0f8b5796b7a`). It preserves all other
operations and the six lifecycle response-style type hooks. Regenerate it with:

```sh
SDK_OPERATION_SCOPE="$PWD/openapi/sdk/trial-stability-source.json" \
  scripts/generate-oss-sdk.sh /path/to/core-at-32ea09fa/api_contracts/openapi/swagger.json
```

`include_trial_stability` remains optional. Generated Python models and
TypeScript types expose the optional `trial_stability` array and its nullable
statistics; the facade and transport are unchanged. The SDK overlay keeps
existing schema properties in their previous order and appends new fields so
Python positional model arguments remain compatible. JSON property order has
no API meaning. A narrow Python post-hook keeps the server's documented
`false` default opt-in at the wire: omitted model fields remain omitted, while
explicit `False` is still serialized. The deterministic SDK
fixture is synthetic contract evidence, not a live API receipt.

The metadata-slice refresh is scoped to the same comparison POST using core
PR #3490 (`e0e40ac1eeebd2b91659fa419443c64a2fdb89289`). It adds optional
`metadata_equals` (at most 20 JSON-valued keys), optional `split_name`, and an
optional `selection` receipt containing total and selected plan counts. The
request fields and response receipt remain omitted when the server does not
return them. `openapi/sdk/metadata-slices-source.json` records the reviewed
source revision and operation closure. The generated overlay retains the
existing trial-stability and release-gate model types; this slice does not
introduce storage, transport, or a second comparison API.

This SDK PR stacks on open compatibility PR #25 (`44f99aa`) and ports dev's dataset retry hardening (`1607f12`) without replacing its package-version fallback. PR #25 remains an independent integration prerequisite; this slice does not merge its generated Go/Java surface or publish packages.
