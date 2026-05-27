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
