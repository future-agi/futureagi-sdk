# Changelog

All notable changes to `futureagi-sdk` are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed: CLI install hints
- Python CLI missing-dependency errors now name the unique extra that supplies the
  import, including `futureagi[evals]` and Python 3.11+ for local evaluations.
  The local-evals Python-version guard reports `MISSING_EXTRA` (exit 3); missing
  non-extra imports in file and module code-object targets report usage errors
  (exit 2), without an unrelated experiments install hint.

### Client families and versioning
- Keep the released Python `fi.Client` / `fi.AsyncClient` as the same classes as
  `fi.platform.Client` / `AsyncClient`, and TypeScript root `Client` as
  `platform.Client`. These are not aliases for `FutureAGIClient` or
  `AsyncFutureAGIClient`; both families remain available.
- The facade changes below describe the `FutureAGIClient` family and legacy
  helpers unless explicitly labelled as the released platform client family.
  Their errors, response envelopes and paging contracts are distinct.
- Package versions remain release-please-managed. The facade notes are
  unreleased changes, not an announcement of Python 0.7.0 or TypeScript 0.2.0.

### Changed: agent-learning-kit namespace (Python only)
- The separate `agent-learning-kit` distribution owns `fi.alk` and all of its
  subpackages. The Python SDK no longer ships any `fi/alk/` file in its source
  tree, wheel or sdist; its platform `fi.evals` API remains available.
- `fi.simulate` and `fi.opt` remain clear-error stubs pointing to
  `fi.alk.simulate` and `fi.alk.opt`. Moved evaluation names and the report module
  now name their exact `fi.alk.evals` replacements. The SDK neither imports nor
  installs ALK and retains namespace extension for separate install paths.

### Python experiment trace export
- Uploaded Python experiments with SDK-owned tracing now raise `TraceExportError`
  (`TRACE_EXPORT_FAILED`, CLI exit 3) and emit one `TraceExportWarning` per run when
  an OTLP batch fails, including collector HTTP 404/405/5xx and connection failures.
  Warning promotion never replaces the typed error or an existing primary failure, including
  interruption. Diagnostics name the endpoint and status without response bodies or secrets;
  nonconnection request failures remain non-retryable instead of becoming connection errors.
  The error suggests `trace=False` (CLI `--no-trace`) for future runs without tracing.
  Run items may already be stored; spans are not journaled and resume cannot recover them.
  `futureagi-py doctor` now checks `/tracer/v1/traces`: a missing route (HTTP 404) is a setup
  problem; transport exceptions remain inconclusive ("could not check") without changing its
  exit code. A GET response is explicitly not proof that POST export works.
  Batch-processor queue drops and HTTP 200 OTLP partial rejections are not covered by this
  terminal-batch check. Caller-owned exporters and the TypeScript SDK are unchanged.

### Python unsupported legacy helpers
- **Python unsupported legacy helpers report the server limitation explicitly.**
  `EvalTemplateManager.get_ground_truth_config`, `set_ground_truth_config`,
  `search_ground_truth` and `fi.client.Client.log` retain their signatures and raise
  `fi.errors.PlatformNotConfiguredError` (`code="unsupported_operation"`) before HTTP.
  The config/search and model-log routes were absent at v1.56.1;
  they have no compatible replacements in platform 2.0.0.
  `list_ground_truth(template_id)` reads
  dataset state, not the old template config (`mode` and `injection_format` are
  unavailable). Atomic setup requires both mappings and cannot set `mode`,
  `similarity_threshold` or `injection_format`. `get_ground_truth_data` reads
  paginated rows, not similarity-search results. For tracing, use traceAI
  instrumentation to emit traces and `client.tracing` on a `FutureAGIClient` to
  query them; neither accepts the old model-log payload as a drop-in replacement.
  `Client.log` was present in futureagi 0.6.13; that wheel did not contain
  `fi.evals` or these ground-truth helpers. TypeScript has no corresponding helpers.

### Licensed operations and HTTP 402
- On `FutureAGIClient`, HTTP 402 now raises `PaymentRequiredError`; `402 LICENSE_MISSING` raises its
  `LicenseRequiredError` subclass, still catchable as `FutureAGIAPIError`. The message
  asks this server's administrator to configure an Enterprise licence, without
  claiming that hosted deployments lack the feature. Other 402 codes remain payment/
  entitlement errors and keep their server code and payload.
- Missing-licence messages name the server-reported feature when available. Tracing
  examples explain the licence requirement before calling error-feed operations;
  Python's built-in error help includes the error tree and legacy namespace caveat.
- Document Enterprise licensing for error-feed methods (`tracing.issues`, `issue`,
  `issue_stats` / `issueStats`) and generated feed operations. Self-hosted servers
  need a licence; cloud availability depends on the plan. Dataset user-eval methods
  document their conditional Turing/Protect model gate (`ENTITLEMENT_DENIED`, not
  `LICENSE_MISSING`); code evaluations are exempt. Generated docs use reviewed
  licensing overrides. Existing error exports are retained.
- Document the same conditional model gate on legacy `Dataset.add_evaluation` /
  `Dataset.addEvaluation` and Python-only `EvalTemplateManager.run_playground`.
  Their published `DatasetError` / `Exception` contracts are unchanged.

### Console API availability errors
- Console calls that receive a completely read 404 without a Console/EE API error envelope now raise
  `ConsoleUnavailableError`, a `NotFoundError` subclass. The diagnostic names only
  the host and explains how to set or check the Console API origin; no preflight
  request is added. Genuine resource 404s and `ProductNotAvailableError` are unchanged.
- Hosted Future AGI does not support Console access through the SDK in this release.
  For self-hosted Enterprise, set `FI_PLATFORM_BASE_URL` to the Console API origin;
  if explicitly configured, check that URL. Python's saved-login origin diagnostic
  points to the saved login rather than an environment or constructor setting.
- Capped or interrupted 404 bodies do not prove Console unavailability; when the EE
  envelope cannot be parsed, both SDKs retain status-only `NotFoundError` classification.
  This also applies to oversized HTML error pages, even with a `text/html` content type.

### Fixed: published compatibility (Python only)
- Restore all 32 Python queue model camelCase output aliases from 0.6.13 for
  `model_dump(by_alias=True)` and `model_dump_json(by_alias=True)`, including
  nested `DefaultQueue` results. Default and `by_alias=False` dumps remain
  canonical snake_case; validation precedence, warning-once behavior, allowed
  extras and request payloads are unchanged. Serialization-mode schemas honor
  the output aliases; validation-mode schemas are unchanged.
- Pin output names independently of accepted inputs using the published wheel's
  AST. This is an unreleased Python correction, not a TypeScript behavior change
  or a change to the immutable published packages.

### Fixed: TypeScript catalog response declarations
- Correct core `FutureAGIClient` return types to describe response bodies, not the
  fetch client's metadata wrapper. Alert operations now distinguish success
  envelopes, bare DRF reads, and no-content deletes.
- Correct the success-envelope types for queue archive, dataset row/column
  deletion, dataset evaluation/template deletion, and experiment deletion;
  correct the DRF page types for both annotation-label list aliases
  (`annotationLabels.list` / `scores.labels.list`).
- Declare `total_pages` and `current_page` on alert-log, annotation-queue/item,
  experiment, score, and prompt/label/version pages. Prompt-version lists always
  return pages; remove their unreachable array type alternative.
  The TypeScript changelog lists the affected methods and payloads.
- No runtime return shapes change in either SDK. Python already preserves these
  bodies. Published 0.1.2 APIs, tracing/dashboard behavior and the low-level
  generated API are unchanged; the corrected facade methods remain unreleased.

### Fixed: dataset payloads (unreleased)
- Python `add_run_prompt` and TypeScript `addRunPrompt` send `max_tokens`,
  `temperature`, `presence_penalty`, `frequency_penalty` and `top_p` under
  `config.run_prompt_config`, matching the server's generation-setting readers.
  Model, messages, output format, concurrency, tools, tool choice and response
  format stay directly under `config`. Explicit zero values are retained;
  Python also retains explicitly supplied empty tools and response formats.
- TypeScript `addOptimization` sends `promptColumnName` as `prompt_name` alongside
  its already-canonical `name`, retaining column/evaluation lookup and mapping.
  Public argument names, order, types, defaults, validation and return identity
  are unchanged. These are client payload fixes in the upcoming packages, not a
  server regression or a change to published Python 0.6.13 / TypeScript 0.1.2.

### Fixed: published compatibility
- Restore all six `BulkAnnotationResponse` fields from Python 0.6.13 and TypeScript
  0.1.2: `annotationsCreated`, `annotationsUpdated`, `notesCreated`, `succeededCount`,
  `errorsCount`, `warningsCount`. Both spellings accept and expose the same values;
  Python retains the published model fields and serialization names.
- Restore the published queue model inputs (Python) and properties (TypeScript),
  retaining snake_case fields and each Python model's existing extra-field policy:
  - `QueueDetail`: `assignmentStrategy`, `annotationsRequired`,
    `reservationTimeoutMinutes`, `requiresReview`, `createdAt`, `updatedAt`,
    `itemCount`, `completedCount`.
  - `QueueItem`: `sourceType`, `sourceId`, `assignedTo`, `createdAt`.
  - `QueueProgress`: `inProgress`, `progressPct`, `annotatorStats`.
  - `QueueAnalytics`: `annotatorPerformance`, `labelDistribution`, `statusBreakdown`.
  - `QueueAgreement`: `overallAgreement`, `perLabel`, `annotatorPairs`.
  - `Score`: `labelId`, `labelName`, `scoreSource`, `annotatorId`, `annotatorName`,
    `sourceType`, `sourceId`, `createdAt`.
  - `ExportToDatasetResponse`: `datasetId`, `datasetName`, `rowsCreated`.
- Restore Python `fi.datasets.dataset.EvalInfoResponseHandler` and `EvalTemplate`
  as re-exports of their supported eval implementations, including public members.
- Restore TypeScript dataset properties and matching helper/client inputs:
  `Column` / `ColumnType` (`dataType`, `sourceId`, `isFrozen`, `isVisible`, `evalTags`,
  `averageScore`, `orderIndex`); `Cell` / `CellType` (`columnId`, `rowId`, `columnName`,
  `valueInfos`, `failureReason`); `DatasetConfig` / `DatasetConfigType` (`modelType`,
  `columnOrder`); `HuggingfaceDatasetConfig` / `HuggingfaceDatasetConfigType`
  (`numRows`); `DatasetTable` / `DatasetTableType` (`datasetConfig`). `createColumn`,
  `createCell`, `createRow`, table CSV conversion and dataset response parsing retain
  legacy values while canonical wire payloads remain snake_case.
- Restore TypeScript knowledge-base properties: `KnowledgeBaseConfig.lastError`,
  `KnowledgeBaseCreateResponse` (`kbId`, `kbName`, `fileIds`, `notUploaded`),
  `KnowledgeBaseUpdateResponse.notUploaded`, and
  `KnowledgeBaseListResponse.result.tableData` with its required item ids.
- Restore TypeScript `AnnotationQueue.addLabel(queueId, labelId, options?)` and
  `removeLabel(queueId, labelId, options?)` alongside the named-options forms.
  Published overloads, required inputs, properties and return types are pinned
  directly from archived declarations; no new arguments are required.

### Fixed: published compatibility and legacy pagination
- Restore Python 0.6.13 imports of `fi.api.auth.DatasetNotFoundError` and
  `fi.client.HttpMethod`, `RequestConfig`, and `Routes` as the same canonical objects.
- Preserve legacy queue list `page_size` / `pageSize` arguments and defaults in
  Python and TypeScript. Queue and item lists send the server's `limit` query key
  while retaining 1-based `page`; project, dataset and eval pagination is unchanged.
- Python queue `create` displays `OMITTED_LABEL_IDS` instead of an object address in
  its signature.

### Package ownership repair guidance
- Offline doctor suggests destructive repairs only after a bounded, symlink-free
  audit of removal paths, derived bytecode and supported namespaces. Shared or
  uncertain ownership, legacy scripts and unproven entry-point wrapper removals
  receive manual guidance instead: back up or restore supported files, repair
  with the original installer, then re-run doctor. Doctor never performs repairs.
- Suggested uninstall commands no longer pass `-y`; pip retains its confirmation
  prompt. SDK reinstall guidance remains limited to `--no-deps`.

### Packaging (unreleased)
- The Python SDK installs the `futureagi-py` console script (not `futureagi`, which is the
  standalone Future AGI CLI); `python -m fi._cli` runs the same CLI. The distribution
  (`pip install futureagi`), `import fi` and the `futureagi.cli` plugin group are unchanged.
- Python requires 3.10 or newer (tested support: 3.10–3.13), declares `anyio`,
  and includes the `fi/py.typed` marker. Python 3.14 is not yet claimed.
- TypeScript requires Node 18 or newer. The root and webhooks support ESM and
  CommonJS; legacy TypeScript resolution has explicit subpath mappings.
- The gateway data-plane client ships in both candidates: wheels and sdists
  include `fi.gateway` (and declare `typing-extensions`, which it imports), and
  staged npm tarballs include `dist/gateway` with the `@future-agi/sdk/gateway`,
  `/gateway/testing`, `/gateway/express`, `/gateway/nextjs` and `/gateway/react`
  subpaths, resolved with the default `import`/`require` conditions. React
  17–19 is an optional peer, needed only by `/gateway/react`. Shipping the
  client is not live gateway qualification.
- Webhooks remain in the one SDK; the standalone source fixture is not buildable
  as a distribution. No automation publishes, tags or deploys these candidates.
- Platform namespaces remain 0.x APIs. The gateway client keeps its
  compatibility promise: no breaking change below 1.0.

### Simulation facade scope

- Only the Python `fi.simulate` facade is withdrawn; its clear-error stub points
  to `fi.alk.simulate`. The released Python and TypeScript platform clients keep
  their `client.simulation` resource, with no alias to the facade or ALK.

### Changed
- List methods on `FutureAGIClient` now document their accepted pagination parameters
  and page-number bases. Generated tracing and integration operations no longer
  declare unsupported pagination dialects; documented server-supported size aliases
  remain available. Free-form paging parameters are sent unchanged for the server
  to validate, without silently converting between zero- and one-based pages.
  Alert details also accept zero-based pagination for their nested log list.
- Generated prompt-label lookup clients declare `template_id` and `template_name`
  selectors without advertising unsupported pagination; existing template lookup
  facades remain type-safe.
- **Python ground-truth mapping setters now use atomic `PUT /model-hub/ground-truth/{id}/setup/`.**
  Breaking change: two-argument calls now raise before HTTP unless the other mapping,
  `max_examples` (1–20) and `enabled` are also passed as keywords. Read current state
  with `list_ground_truth(template_id)` and preserve unchanged values; setup is a
  complete replacement, not a patch. Missing/invalid setup arguments and unknown
  role keys raise `fi.errors.ConfigurationValueError`, a subclass of both
  `ConfigurationError` and `ValueError`. Accepted roles are `output` and
  `explanation` (legacy aliases `expected_output`, `reasoning`, `reason`); the
  `input` and `score` roles documented by ai-evaluation 1.1.0 are not accepted
  by the platform's setup and now raise.
  Server side effects: setup makes this dataset the template's ACTIVE ground truth
  and deactivates the others for the same template, organization and workspace,
  even when `enabled=False`. A `variable_mapping` change on a COMPLETED dataset
  resets `embedding_status` to PENDING; re-run
  `trigger_ground_truth_embeddings(ground_truth_id)` afterward.
  Removed config/search and legacy `Client.log` calls raise
  `PlatformNotConfiguredError` before HTTP. For tracing, use traceAI instrumentation
  to emit traces and `client.tracing` on a `FutureAGIClient` to query them; neither
  is a drop-in model-log replacement. Retired `Routes` constants remain available
  for source compatibility with ai-evaluation 1.1.0 but are never called.
- **Annotation queues: `create()` resolves at least one label id before creating the named queue.**
  Prefer explicit ids: Python `AnnotationQueue.create(name, label_ids=[...])` and
  `FutureAGIClient.annotation_queues.create({"name": ..., "label_ids": [...]})`; TypeScript
  `AnnotationQueue.create({ name, labelIds })` and `annotationQueues.create({ name, label_ids })`.
  Omitted ids use exactly one project, dataset or agent-definition scope to look up
  `get_or_create_default` / `getOrCreateDefault` and copy its labels, emitting one
  `DeprecationWarning` that explicit ids will be required. The lookup can create or
  restore the default queue even if the label check then fails; the new named queue
  remains unscoped. No label is invented: absent or ambiguous scope, or no usable
  labels on its default queue, raises `DefaultQueueLabelError` (`ValueError` in
  Python; `SDKException` in TypeScript). Import that same constructor from `fi` /
  `fi.queues` in Python or `@future-agi/sdk` in TypeScript. Explicit ids avoid the
  lookup and omission warning. The server already refused a queue
  without labels ("At least one label is required."); the SDK now rejects invalid explicit ids
  before a request: Python raises `TypeError` / `ValueError`, TypeScript throws `SDKException`.
  Required values are validated before the named queue is created:
  a facade body without `name` now raises `ValueError` / throws `SDKException` instead of failing
  inside the generated model or at the server, and Python `AnnotationQueue.create(name=None, ...)`
  (or `label_ids=None`) raises `ValueError`, as TypeScript `AnnotationQueue.create` throws. A facade label or annotator id that is not a UUID
  now raises a `ValueError` naming `annotation_queues.create()` instead of the generated model's
  bare "badly formed hexadecimal UUID string". Both `create()` methods also take `auto_assign`, `annotator_ids` and
  `annotator_roles` (`autoAssign`, `annotatorIds`, `annotatorRoles`), which the server accepts.
- **Annotation queues: `create()` refuses `project_id`, `dataset_id` and `agent_definition_id`.**
  A create has no such fields, and the server never applies them to the queue (it only uses them
  to scope its duplicate-name check), so the queue was created unscoped without an error, its name
  checked against the wrong queues. `FutureAGIClient.annotation_queues.create` (a body key, or a
  generated model's `additional_properties`) now raises `ValueError`; TypeScript
  `annotationQueues.create` and `AnnotationQueue.create` (`projectId`, `datasetId`,
  `agentDefinitionId`, or the snake_case spelling) throw `SDKException`. The message names the
  `get_or_create_default` / `getOrCreateDefault` call to use, with the id filled in.

- `MissingAuthError` now lives in `fi._credentials` (the clients no longer import `fi.utils`).
  `fi.utils.errors.MissingAuthError` is the same class only while futureagi's own `fi/utils` is
  installed: agent-learning-kit and ai-evaluation ship their own `fi/utils/errors.py`, and with
  one of them installed over futureagi that name is a different class. Catch
  `fi.errors.AuthError` (or `fi.errors.CredentialsMissingError`) instead.
- **Typed errors on every namespace (Python).** Each HTTP status raises one `fi.errors` class on
  core and platform namespaces alike: `BadRequestError` 400, `AuthenticationError` 401,
  `PermissionDeniedError` 403, `NotFoundError` 404, `ConflictError` 409, `PayloadTooLargeError` 413,
  `UnprocessableEntityError` 422, `RateLimitError` 429, `ServerError` 5xx. All are still
  `FutureAGIAPIError`, so existing `except` clauses keep working. A status the API spec does not
  declare (a 429 or 503 from a proxy) is now one of these instead of the generated client's
  `UnexpectedStatus`, and an HTML error page no longer raises `JSONDecodeError`. On core
  namespaces, `payload` is now the raw response body (not the generated error model's dict). A
  failure with no response raises `fi.errors.APIConnectionError` / `APITimeoutError`, which is
  also the exact httpx class it replaces (`except httpx.ConnectError` keeps working).
- **Typed errors on every namespace (TypeScript).** Core namespaces throw typed classes
  (`NotFoundError`, `CoreRateLimitError`, `CoreServerError`, ...) instead of the parsed response
  body; the body's fields are copied onto the error, so code that reads `e.detail` keeps working.
  Missing keys throw `CredentialsMissingError` (same message). The package root's released
  `RateLimitError` and `ServerError` remain the dataset constructors, still `DatasetError`
  instances; `DatasetRateLimitError` and `DatasetServerError` are aliases of those same classes.
  `FutureAGIClient` core transports use the distinct `CoreRateLimitError` / `CoreServerError` root exports
  (and error names), both `FutureAGIAPIError` subclasses. The released `Client` uses its separate
  `platform` error tree.
- **Dataset error compatibility (Python).** SDK-owned `fi.utils.errors.RateLimitError` and
  `ServerError` also subclass the corresponding `fi.errors` classes, while retaining
  `DatasetError` membership and the released `(message=None, cause=None)` constructors.
  No `fi.RateLimitError` / `fi.ServerError` root aliases are added. Legacy calls carry no response
  metadata: inherited status fields use nominal 429 / 500 and `payload=None`, not an observed
  5xx status. The separate dataset 503 `ServiceUnavailableError` is unchanged. This hierarchy
  applies only while futureagi's `fi/utils/errors.py` is installed; an older sibling distribution
  overwriting that file removes the compatibility, but does not change `fi.errors`.
- **Retries are per operation (platform namespaces).** Each platform operation gets one of four
  retry classes from the API contract: `keyed` (an idempotency key, minted once and sent on every
  attempt; 429, 502-504 and network errors are retried, and a request still in progress is waited
  out), `keyed-not-durable` and `unsafe` (429 and errors before anything was sent only, never a
  5xx), `http-idempotent` (429, 502-504 and network errors). Platform calls never follow a
  redirect, so the keys never reach another origin.
- **No namespace follows a redirect.** A 3xx raises `UnexpectedRedirectError` (Python
  `fi.errors`, TypeScript package root) naming the redirect's host only, on core and platform
  namespaces in both languages. TypeScript core namespaces used to follow a redirect and send
  `X-Api-Key` / `X-Secret-Key` to its target; they are now built with `redirect: "manual"`, so
  even a same-origin redirect (a trailing slash) is an error instead of being followed. Python core
  namespaces never followed one; a 3xx used to surface as a JSON parse error, or as `None` from
  `users.current()` and the other raw calls.
- **The platform key pair comes from one place.** Both arguments, or both `FI_API_KEY` /
  `FI_SECRET_KEY` (or, in Python, the saved login): with one key as an argument the other half is
  never taken from the environment, and platform calls raise `CredentialsMissingError` saying so.
  TypeScript core namespaces keep their current resolution.

### Deprecated
- The restored camelCase model spellings above remain supported; prefer their
  snake_case equivalents (for example `annotations_created`, `in_progress`,
  `data_type`, `last_error`, `table_data`). SDK validation, helpers and response
  adapters warn once per process per alias when a legacy input or attribute is
  used, naming its replacement. Canonical-only use is silent. TypeScript's erased
  interfaces carry `@deprecated` guidance; plain user-created objects cannot warn.
- TypeScript legacy response properties are synchronized, non-enumerable views;
  serialization of canonical SDK responses does not add duplicate camelCase keys.
  Python queue extras remain allowed and bulk annotation extras remain ignored.
- Omitting annotation queue label ids emits one `DeprecationWarning` that explicit ids will be
  required. Legacy `project`, `dataset` and `agent_definition` (TypeScript `agentDefinition`)
  remain accepted for default-label lookup. With explicit labels, passing a scope field emits
  a warning that the field is read-only on create and is not sent. A create never scopes a queue;
  for the default queue itself, call `get_or_create_default(project_id=...)` (TypeScript
  `getOrCreateDefault({ projectId })` / `annotationQueues.getOrCreateDefault({ project_id })`).

### Added
- Release chain to the docs: `publish.yml` dispatches `sdk-release` (`stage: released`) to future-agi/docs after a package is on its registry, and `release-please.yml` dispatches `stage: candidate` when a version PR is prepared, so the docs repository opens or marks ready one reference PR per release (see `sdkgen/RELEASING.md`, "Downstream: the docs reference").
- `sdkgen/sync_contract.py` stops with the operations named when a backend release removed or moved an endpoint the catalog still exposes, instead of writing a slice that silently loses methods.
- **Python gateway stream context managers:** `Stream` supports `with` and
  `AsyncStream` supports `async with` for chat and text completions. Exiting
  closes the HTTP response and discards unread chunks, including on early exit
  or a body exception, without suppressing that exception. Closing is idempotent;
  closed streams and retained iterators are exhausted, including cache-hit JSON
  streams. Closing while another thread or task is reading also releases the
  response without a generator-busy error. A pending read may report a transport
  interruption; wait for that reader to finish before iterating again. The
  TypeScript gateway's existing `abort()` API is unchanged.
- **Connectors, integrations and credential metadata:** `client.connectors`,
  `client.integrations` and read-only workspace metadata through `client.credentials`
  in Python and TypeScript, with TypeScript subpaths `@future-agi/sdk/connectors`,
  `@future-agi/sdk/integrations` and `@future-agi/sdk/credentials`. All three connector
  features are ON in these release artifacts. `client.connectors` and `client.credentials`
  call the Console workspace API (`{FI_BASE_URL}/omega/api`, or `FI_PLATFORM_BASE_URL`):
  they work against self-hosted EE; hosted access through the SDK is not available yet.
  SDK authentication remains on `client.auth`, separate from workspace credential metadata.
- **Annotation queues: the default queue of a project, dataset or agent definition.** Python
  `AnnotationQueue.get_or_create_default(project_id=...)` (returns `DefaultQueue`) and
  `FutureAGIClient.annotation_queues.get_or_create_default(project_id=...)` (returns the response
  body as a dict, `{"status": ..., "result": {...}}`, like the client's other methods); TypeScript
  `AnnotationQueue.getOrCreateDefault({ projectId })` and
  `annotationQueues.getOrCreateDefault({ project_id })` (the body, as in Python). Each takes
  exactly one of a project, dataset or agent definition id (`dataset_id` / `datasetId`,
  `agent_definition_id` / `agentDefinitionId`) and refuses anything else before the request; the
  Python facade also checks that the id is a UUID and names the call when it is not. The server
  returns the active default queue, restores an archived one, or creates it, with its labels
  (`POST /model-hub/annotation-queues/get-or-create-default/`).

### Added (webhooks)
- `fi.webhooks.verify` (standard library only) and TypeScript `verifyWebhook` (also at `@future-agi/sdk/webhooks`):
  verify Standard Webhooks v1 requests from Future AGI; both pass the language-neutral signing conformance vectors.
- Receivers verify with `fi.webhooks.verify` from `futureagi`; no separate webhooks distribution is published.
- `fi.webhooks.Webhooks` / `AsyncWebhooks`: endpoints, test deliveries, the delivery log, redelivery, secret
  rotation, the events list, the event catalog and the webhook policy.
- `futureagi-py webhooks list|get|create|update|enable|disable|test|deliveries|delivery|redeliver|rotate-secret|
  revoke-previous-secret|delete|events|verify`; secrets are printed only to a terminal or written to a 0600 file.

### Added (extra headers)
- `FI_EXTRA_HEADERS` (`Name=value` entries, `;` or newlines between) and an `extra_headers=` argument (TypeScript
  `extraHeaders`) on every client: headers sent on every request to the Future AGI base URL and never to another
  host. For environments behind a proxy such as Google IAP (`Proxy-Authorization: Bearer <identity token>`). The SDK's
  own `X-Api-Key`, `X-Secret-Key` and `Authorization` cannot be set this way; values are never logged or traced.
  A control character in a name or value (CR, LF, NUL, tab or any other) and a name with `:` or whitespace are
  refused (`EXTRA_HEADERS_INVALID`), so no value can add a second header line.
- `fi.api.auth.APIKeyAuth` keeps a caller's `default_headers` (it raised `TypeError` before); the SDK's keys win.

### Added (released platform client family)
- `fi.Client` / `fi.AsyncClient` (Python) and `new Client()` (TypeScript, `@future-agi/sdk`): one generated client covering all 158 platform operations, generated by `sdkgen/` from the API contract and a catalog whose operation names match the monorepo's MCP tools (the MCP server itself stays in the monorepo).
- Hand-written extension points on the generated client: per-resource modules under `fi/platform/resources/` and `src/platform/resources/` (scaffolded once, never regenerated), replaceable resource classes (`Client._resources`, `new Client({ resources })`), `client.request()` for endpoints the catalog lacks, and per-call `RequestOptions` (headers, timeout, retries) next to `extra_query` / `extra_body`.
- `client.spans.ingest()` (both SDKs): send spans straight to the tracer.
- `fi.gateway`: the Agent Command Center data-plane client (vendored from `agent-command-center-sdk`), `Gateway` / `AsyncGateway`.
- CI: `ci.yml` (generated code current, catalog MCP names checked against the monorepo's tool list at the pinned backend release, Python 3.9/3.11/3.13 unit suite, TypeScript type check, tests and build) and `e2e.yml` (the live suites against the Standalone backend, booted from the monorepo's compose files and the released image, with a fresh account from `sdkgen/local_api_key.py --signup`). `FI_E2E_REQUIRED=1` turns a skipped live suite into a failure.
- Release cycle: a backend release is synced in by the monorepo's `sdk-sync` workflow (contract slice, regenerated clients, `sdkgen/contracts/BACKEND_VERSION`), promoted from `dev` to `main` (`promote.yml`), versioned by release-please (`python-vX.Y.Z`, `typescript-vX.Y.Z`, per-package changelogs) and published to PyPI and npm (`publish.yml`).

- `pr-title-lint.yml`: pull request titles must follow Conventional Commits, since squash-merged titles are what release-please versions from. `publish.yml` installs the just-published package from PyPI and npm into a clean environment and runs a quickstart (CommonJS and ESM for npm) before the release counts as done.
- Two knowledge-base resources, one per backend store: `client.knowledge_bases` (`/model-hub/kb/`: list, get, and now create, update, delete, so the id a create returns is one get finds) and `client.file_knowledge_bases` (`/model-hub/knowledge-base/`, the app's Knowledge Base page: create with uploads, update, list, list_names, delete, `.files.list`, `.files.delete`; the operations formerly under `knowledge_bases`).
- `JsonValue` (TypeScript, from `@future-agi/sdk/platform`; `Any` in Python): request fields the backend accepts as any JSON value (`prompts.run(is_run="prompt")`, `scores.create(value=0.7)`) are typed that way instead of object-only.
- CI: `Packages as installed` builds the wheel and the npm tarball, installs each into an empty environment and runs / type-checks a consumer file there (`python/consumer/consumer.py` with `mypy --strict`, `typescript/futureagi/consumer/consumer-types.mts` with `tsc --strict` against the published `.d.ts`; `pnpm run check:consumer`).
- The generated code is public where users meet it: `fi.platform.models` is a real module (`python/fi/platform/models.py`), the resource base classes live in `fi.platform.resources.base` (nested resources such as `client.datasets.rows` are these classes), and the per-call `Operation` constants moved to the private `fi.platform._operations`. In TypeScript the same split is `src/platform/{models,_operations}.ts` and `src/platform/resources/base.ts`, with two new package subpaths: `@future-agi/sdk/platform` (the client, the resource classes and base classes behind `client.<name>`, every method's `params` type, errors, paging) and `@future-agi/sdk/platform/models`. The scaffolded resource classes carry a docstring. This is what the docs site's API reference reads, so the reference lists every generated method and model instead of empty classes.
- `docs/sdk-reference/`: the platform SDK reference for docs.futureagi.com, generated by the new `docs` target of `sdkgen/generate.py` (one page per resource with every method's parameters, signatures, return model and REST endpoint, Python and TypeScript examples; one response-models page per product area; and a sidebar group organised by product area). The docs repository syncs it with `scripts/sync-sdk-reference.mjs`.

### Fixed
- Platform client, both languages: a redirect is followed only within the client's own origin; one that leaves it raises `APIConnectionError` instead of forwarding `X-Api-Key` / `X-Secret-Key` to the other host. The policy is set on every request, so an injected `httpx.Client(follow_redirects=True)` is held to it as well.
- Platform client, Python: `Client(strict_responses=True)` rejects a response that misses a field the contract marks required (`ResponseValidationError`), instead of returning a model with `None` there; the default client stays tolerant. The generated models list those fields in `__required__`.
- Platform client, both languages: a PATCH is a partial update: `dashboards.update(id, description=...)` no longer demands `name` (the generator makes every PATCH body optional; a PATCH that does need fields says so in the catalog).
- Platform client, both languages: `dashboards.create` / `dashboards.update` return the dashboard detail (with `id`), `prompts.run` the execution receipt (with `template_id`), `evals.configs.create` the id, `optimizations.create` the run; the contract documented the request serializers as the responses (`contract_fix.returns`).
- Platform client, both languages: `client.request(..., unwrap=None)` (`{ unwrap: null }`) returns the body exactly as sent; the automatic `{status, result}` removal applies only when no explicit choice was made.
- Platform client, both languages: `to_list(limit=0)` / `toArray(0)` fetch nothing. TypeScript: a `page` value in `extraQuery` no longer pins every fetch of a pager to that page.
- Platform client, both languages: an explicit `None` / `null` in a request body is sent as JSON `null` (it clears a nullable field); only an omitted argument (`NOT_GIVEN` / `undefined`) is left out. Query strings and form fields still drop it.
- Platform client, both languages: per-call and client header overrides merge case-insensitively, so `x-workspace-id` replaces `X-Workspace-Id` instead of being sent twice.
- Platform client, both languages: `annotation_queues.export(export_format="csv")` returns the CSV text instead of failing on JSON decoding (`operation.decode: auto` in the catalog; `client.request(..., decode="text")` for hand-written calls).
- TypeScript platform client: a 429/5xx response body is released before the retry wait, and a body that fails mid-read (dropped connection, timeout) is handled as a transport error (retried when safe, else `APIConnectionError`) instead of escaping as a raw rejection.
- `fi.gateway`: a streaming call (`stream=True`, `.stream()`, the Responses and legacy completions streams) now counts in the active session (request, tokens from the final usage event, cost from the response headers) and reaches the callbacks (`on_request_start`, `on_stream_start`, `on_stream_chunk`, `on_stream_end` with the reassembled completion, `on_request_end`; `on_error` on failure), the way a plain call does; `redact_messages=True` also redacts tool-call arguments (`messages[].tool_calls[].function.arguments`, `function_call.arguments`); `to_response_format()` keeps a property named `default` (only the JSON Schema `default` annotation is removed). Earlier fixes: `redact_messages=True` now reaches the callbacks; sessions are per thread / asyncio task and restore the outer session on exit; `to_response_format()` emits a schema strict mode accepts; `responses` and `completions` streams decode their own events; finished streams close their response; an async stream can be resumed after an early `break`; `create_mock_client()` never touches the network; base64 embeddings parse; a client made by `with_options()` closes the pool it owns. Details in `python/fi/gateway/VENDORED.md`.
- TypeScript package: `form-data` and `@jest/globals` are now declared, so a fresh `pnpm install` builds and tests.
- TypeScript package: `require("@future-agi/sdk")` works. The CommonJS build under `dist/src/` had no `package.json` of its own, so the root `"type": "module"` made Node load it as ESM and fail on the first `require("./api")`. The build now writes `{"type": "commonjs"}` there.

---

## [0.1.0] — 2026-04-23

First public release. Platform SDK for datasets, prompt workbench, knowledge base, and experiments.

### Added
- **Dataset management** — create, version, add rows/columns, attach evaluations programmatically.
- **Prompt Workbench** — version control, A/B testing via labels, compile with variable substitution.
- **Knowledge Base** — create, update, delete knowledge bases with PDF/DOCX/TXT/RTF uploads for RAG.
- **Experiments** — run prompt/model experiments and track results.
- **Python SDK** (`futureagi` on PyPI) + **TypeScript SDK** (`@future-agi/sdk` on npm).

---

[Unreleased]: https://github.com/future-agi/futureagi-sdk/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/future-agi/futureagi-sdk/releases/tag/v0.1.0
