# Changelog

## Unreleased

### Fixed: released root error identities
- Root `RateLimitError` / `ServerError` retain the released dataset constructor identities,
  so dataset errors still match existing `instanceof` checks and catch branches.
  `DatasetRateLimitError` / `DatasetServerError` remain aliases of these same constructors.
- `FutureAGIClient` core-transport errors are exported as `CoreRateLimitError` / `CoreServerError`,
  with matching error names and unchanged `FutureAGIAPIError` membership. The released
  `Client` / `platform` error tree is separate and unchanged.

### Clarified: credential isolation
- `APIKeyManager` remains process-wide and must not be used as a per-tenant store;
  credential isolation applies only to `APIKeyAuth` client instances, and manager
  deprecation is planned for 0.7.x.

### Python companion trace export
- Companion Python 0.7.0 only: SDK-owned experiment trace export failures now raise
  `TraceExportError` (CLI exit 3) with one warning per run; `futureagi-py doctor`
  checks for the collector route without claiming to verify POST export. Warning promotion
  preserves typed and primary errors, and inconclusive doctor transport checks retain their
  prior exit behavior. Nonconnection request failures no longer gain connection retries;
  errors suggest Python `trace=False` / CLI `--no-trace` for future runs without tracing.
  Items may already be stored and resume cannot recover lost spans. Queue drops and HTTP 200
  OTLP partial rejections are outside the terminal-batch check. No TypeScript behavior changes.

### Licensed operations and HTTP 402
- On `FutureAGIClient`, HTTP 402 now raises `PaymentRequiredError`; `402 LICENSE_MISSING` raises its
  `LicenseRequiredError` subclass, still catchable as `FutureAGIAPIError`. The message
  asks this server's administrator to configure an Enterprise licence, without
  claiming that hosted deployments lack the feature. Other 402 codes remain payment/
  entitlement errors and keep their server code and payload.
- Missing-licence messages name the server-reported feature when available. The
  shared tracing guide explains the licence requirement before the TypeScript
  error-feed example.
- Document Enterprise licensing for error-feed methods (`tracing.issues`, `issue`,
  `issue_stats` / `issueStats`) and generated feed operations. Self-hosted servers
  need a licence; cloud availability depends on the plan. Dataset user-eval methods
  document their conditional Turing/Protect model gate (`ENTITLEMENT_DENIED`, not
  `LICENSE_MISSING`); code evaluations are exempt. Generated docs use reviewed
  licensing overrides. Existing error exports are retained.
- Document the same conditional model gate on legacy `Dataset.addEvaluation`,
  retaining its published `DatasetError` contract.

### Console API availability errors
- Console requests returning a completely read 404 without a Console/EE API error envelope throw
  `ConsoleUnavailableError`, exported from `@future-agi/sdk` and extending
  `NotFoundError`. The host-only diagnostic uses the failing response, not a
  preflight request. EE resource errors and `ProductNotAvailableError` are unchanged.
  Hosted Future AGI does not support Console access through the SDK in this release;
  for self-hosted Enterprise, set `FI_PLATFORM_BASE_URL` to the Console API origin,
  or check the URL when already configured.
- Capped or interrupted 404 bodies do not prove Console unavailability; when the EE
  envelope cannot be parsed, retain status-only `NotFoundError` classification. This
  also applies to oversized HTML error pages, even with a `text/html` content type.

### Fixed: published model compatibility
- Preserve the 0.2.0 canonical required fields on `BulkAnnotationResponse`,
  `Column` / `ColumnType`, `QueueProgress`, `KnowledgeBaseCreateResponse` and
  `KnowledgeBaseListResponse`. CamelCase aliases remain optional on caller-owned
  canonical objects; normalized SDK results expose both spellings. Explicit
  `Legacy*` types describe older camelCase objects without weakening 0.2.0 reads.
- Retain the deprecated `Routes.log_model` constant for source compatibility.
  This does not re-enable the retired model-logging operation.
- The Python companion preserves 0.7.0 snake_case fields and output names, including
  `by_alias=True` dumps. This supersedes the earlier unreleased 0.6.13 output-name
  restoration; older inputs remain accepted. Neither package is published by this change.

## [0.2.0](https://github.com/future-agi/futureagi-sdk/compare/typescript-v0.1.2...typescript-v0.2.0) (2026-11-05)


### Features

* revamp eval template management routes and update namespace handling ([90e70a1](https://github.com/future-agi/futureagi-sdk/commit/90e70a1c800c96c3772a213035ad2412561a9659))
* **sdk:** add generated platform clients and guarded releases ([a2e781a](https://github.com/future-agi/futureagi-sdk/commit/a2e781a07d02bdb4b31c0328acd770408d2d5cd4))


### Bug Fixes

* custom eval resolution for evalId=0 and camelCase keys (TH-3610) ([866293e](https://github.com/future-agi/futureagi-sdk/commit/866293edb87362137bb2fc790f80d52a845bd3a8))
* remove leaked credentials, restore null-safety and backward compat in dataset parsing ([8931496](https://github.com/future-agi/futureagi-sdk/commit/8931496fd3c9e0b3fe60925870e4079d8920a4a5))
* resolve custom eval evalId=0 in TypeScript SDK ([2db015a](https://github.com/future-agi/futureagi-sdk/commit/2db015a2b612f735b00ac847aa3c854249349087))

### Fixed: dataset payloads (unreleased)
- `Dataset.addRunPrompt` sends `max_tokens`, `temperature`, `presence_penalty`,
  `frequency_penalty` and `top_p` under `config.run_prompt_config`, matching the
  server's readers. Model, messages, output format, concurrency, tools, tool
  choice and response format remain directly under `config`; explicit zero,
  false and empty options keep their values and omitted options remain absent.
- `Dataset.addOptimization` sends `promptColumnName` as `prompt_name` alongside
  its already-canonical `name`, preserving column/evaluation lookup and mapping.
  Both methods retain public argument names, types, defaults, validation, column
  translation and return identity. These are client payload fixes for the
  upcoming package, not a server regression or a change to published 0.1.2.

### Fixed: published compatibility
- Restore `BulkAnnotationResponse.annotationsCreated`, `annotationsUpdated`,
  `notesCreated`, `succeededCount`, `errorsCount`, `warningsCount`; SDK results
  expose both spellings without requiring snake_case keys on published inputs.
- Restore queue response properties and legacy payload parsing:
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
- Restore dataset properties (including each exported `*Type` alias): `Column`
  (`dataType`, `sourceId`, `isFrozen`, `isVisible`, `evalTags`, `averageScore`,
  `orderIndex`); `Cell` (`columnId`, `rowId`, `columnName`, `valueInfos`,
  `failureReason`); `DatasetConfig` (`modelType`, `columnOrder`);
  `HuggingfaceDatasetConfig.numRows`; `DatasetTable.datasetConfig`.
  Helpers, dataset clients and CSV conversion preserve legacy input values;
  dataset response parsing exposes synchronized legacy properties.
- Restore `KnowledgeBaseConfig.lastError`, `KnowledgeBaseCreateResponse`
  (`kbId`, `kbName`, `fileIds`, `notUploaded`),
  `KnowledgeBaseUpdateResponse.notUploaded`, and
  `KnowledgeBaseListResponse.result.tableData` with required item ids.
- Restore positional `AnnotationQueue.addLabel(queueId, labelId, options?)` and
  `removeLabel(queueId, labelId, options?)` alongside the named-options overloads,
  including the optional timeout. Published properties, inputs, constructors,
  individual overloads and returns are checked against archived declarations.
- Fix 0.1.2 compatibility and legacy pagination: preserve queue list `pageSize=20`
  and item list `pageSize=50`, sending `limit` on the wire with the same 1-based page.

### Fixed: response types (no runtime return-shape changes)
- Core `FutureAGIClient` facade declarations now describe the response body rather
  than the fetch client's `{data, request, response}` metadata wrapper. This covers
  annotation queues and their items/discussion/review, datasets, experiments v2,
  evals, users, and alerts. Dataset-version
  and external experiment-run methods already used data-only declarations.
- `alerts.list`, `create`, `update`, `details`, `bulkMute`, `allLogs` and
  `logsForAlert` now declare their actual `{status, result}` envelopes. `list`
  contains `results` and page metadata; `create` returns a message; `details`
  includes the creator object and log page; `bulkMute` returns `{message}`;
  `allLogs` and `logsForAlert` contain arrays. `get`, `log` and `logs` remain bare
  DRF responses; `delete` has no JSON body. `metricOptions`, `previewGraph`,
  `graph` and `resolveLogs` retain their existing server-envelope schemas.
- `annotationQueues.archive`, `datasets.deleteRow`, `datasets.deleteColumn`,
  `evals.deleteDatasetUserEval`, `evals.deleteDatasetTemplateEval` and
  `experimentsV2.delete` now declare HTTP 200 success envelopes instead of `void`.
  Archive returns deletion/archive flags and the queue id; experiment deletion
  returns a message and deletion count; the other four return messages.
- `annotationLabels.list` and its alias `scores.labels.list` now declare DRF
  pages, not item arrays. Read label items from `.results`, not by calling `.map()`
  on the returned page.
- `alerts.logs`, `annotationQueues.list`, `annotationQueues.items.list`,
  `experimentsV2.list`, `scores.list`, `prompts.list`, `prompts.labels.list` and
  `prompts.versions.list` now declare the complete DRF page, including
  `total_pages` and `current_page` and the nullable `next`/`previous` links.
  Prompt-version listing always returns a page, even without `page` or `limit`;
  its unreachable array alternative has been removed from the declaration.
- These facade methods are new since 0.1.2; their runtime values are unchanged and
  retain the same envelopes as Python. Existing published APIs, tracing/dashboard
  behavior, and the low-level generated API are unchanged.

### Changed
- List methods on `FutureAGIClient` document accepted pagination parameters and
  page-number bases. Generated tracing and integration operations no longer declare
  unsupported dialects; server-supported size aliases remain available. Free-form
  paging queries reach the server unchanged, with no page-base translation.
  Alert details also accept zero-based pagination for their nested log list.
- Generated prompt-label lookup queries declare `template_id` and `template_name`,
  keeping `labels.forTemplate()` type-safe without unsupported paging fields.
- Queue `create` accepts omitted `labelIds` (facade: `label_ids`), with one
  `DeprecationWarning` saying explicit ids will be required. Exactly one legacy
  scope is used by `getOrCreateDefault` to obtain labels; that lookup can create or
  restore the default queue even if the label check then fails, but the new queue
  remains unscoped. If no single scope or no usable labels exist,
  `DefaultQueueLabelError` (an `SDKException`, exported from `@future-agi/sdk`)
  explains why no truthful default is available. Explicit label ids avoid this
  lookup and warning. The legacy project, dataset and agent-definition fields remain
  equally supported for default-label lookup; none scopes the new queue.
- Require Node >=18 and use the @future-agi/sdk package coordinate.
- Support ESM and CommonJS imports for the root and webhooks, with declaration
  files for each format and legacy TypeScript subpath mappings.
- Ship the gateway client in dist/gateway with five entry points
  (@future-agi/sdk/gateway, /gateway/testing, /gateway/express,
  /gateway/nextjs, /gateway/react) that resolve with the default import and
  require conditions, plus legacy typesVersions mappings. React is an optional
  peer, limited to the tested majors 17, 18 and 19, and needed only by
  /gateway/react.
- The default build builds the gateway, the files allowlist includes it, and
  candidate staging keeps its export entries, type mappings and peer. The
  futureagi-gateway-preview resolver condition and the --gateway-preview
  staging flag are gone. Shipping the client is not evidence of live gateway
  qualification.
- Platform namespaces remain 0.x. Gateway APIs retain their
  no-breaking-change promise below 1.0.

### Deprecated
- Prefer the snake_case equivalents of the restored camelCase model fields
  (for example `annotations_created`, `data_type`, `last_error`, `table_data`).
  They remain supported, with `@deprecated` guidance on erased interfaces.
  Runtime adapters/helpers warn once per process per alias on legacy input or
  property use, naming the replacement; canonical-only use is silent.
- Legacy SDK response properties are synchronized, non-enumerable views so
  canonical wire serialization does not add duplicate keys. Plain user-created
  interface objects have no runtime warning mechanism. Canonical input wins
  when both spellings are supplied.

### Not in this release

- Simulation APIs are not offered in this release.

See the repository changelog for API changes.
