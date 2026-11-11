# Changelog

## Unreleased

### Fixed: refused evaluations
- When the eval endpoint refuses an evaluation, `Evaluator.evaluate()` still returns a result,
  and its reason now leads with the server's own message and ends with the HTTP status (for
  example `Validation failed: inputs: ... (HTTP 400)`) instead of the raw response body; a
  body without a message gives a short excerpt. `evaluate(..., engine="turing")` reports the
  refusal as status `failed` with that text as `error` instead of a completed result with no score.

### Fixed: dependency floors
- Raise the base dependency minimums to anyio 4.14.2, certifi 2026.10.18,
  idna 3.15, requests 2.33.0 and urllib3 2.8.0 to exclude versions affected
  by published advisories. Retain the anyio <5 upper bound.

### Fixed: dataset error compatibility
- SDK-owned `fi.utils.errors.RateLimitError` / `ServerError` now also subclass their
  `fi.errors` counterparts, retaining `DatasetError` catches, legacy messages and
  `(message=None, cause=None)` constructors. No `fi.RateLimitError` / `fi.ServerError`
  root aliases are added; the dataset 503 `ServiceUnavailableError` is unchanged.
- Legacy construction has no response metadata: inherited status fields are nominal
  429 / 500 with `payload=None`, not the observed 5xx response. Copy and pickle retain
  the legacy one-message reconstruction; exception causes are not serialized.
- This bridge requires futureagi's own `fi/utils/errors.py`. If an older sibling
  distribution overwrites it, its dataset hierarchy wins; `fi.errors` stays SDK-owned.

- SECURITY: In a process shared by several credentials, the evaluation-template cache inherited from ai-evaluation 1.1.0 could return templates without verifying the secret key (futureagi 0.6.13 shipped no fi.evals); it now uses a digest of the full credentials and normalized base URL, expires after 300 seconds, and never caches failures, so multi-tenant users should upgrade.

### Deprecated: string audio paths
- Bare string audio uploads remain file paths in 0.x and emit a `DeprecationWarning` asking callers to pass `pathlib.Path(...)`. In 1.0, bare strings will raise `TypeError`.
- String paths containing NUL or newline characters are rejected before any file read. Paths are opened read-only, and no request is sent if opening fails. Bytes, binary files, `Path` objects and tuples retain their existing behavior.

### Changed: optional evaluation dependencies
- Local metrics, LLM judges and the `[evals]` dependency set now require Python
  3.11+. The base SDK and cloud evaluation client retain Python 3.10-3.13 support;
  other extras keep their existing Python ranges.
- The `[evals]` LiteLLM dependency is now limited to Python 3.11-3.14 (marker
  `python >=3.11,<3.15`), because LiteLLM does not support Python 3.15 yet. Without
  LiteLLM, every LiteLLM-backed feature (LLM judges and providers, generated grading
  criteria, LiteLLM embeddings for feedback stores) raises `ModuleNotFoundError` naming
  LiteLLM; on Python 3.15+ the message also states the Python limit. Use Python
  3.11-3.14 for these features.
- Raise the LiteLLM floor to 1.100.4 to avoid known vulnerable releases, and exclude
  1.101.0, 1.101.1, 1.101.2, 1.102.0, 1.102.1 and 1.103.0 because of
  GHSA-7hp6-4w63-5g45. Allow OpenAI 2.x (`>=1.109.1,<3`) so clean LiteLLM releases
  can resolve. The separate `[openai]` instrumentation extra is unchanged.
- Require filelock 4.2.1+ for `[evals]`; the security fix has no Python 3.10-compatible
  release. Move rouge-score out of the base installation and into `[evals]`.
  Installing `[evals]` builds rouge-score from its source distribution; base installs
  no longer run that build. Missing ROUGE support now names `futureagi[evals]` and
  Python 3.11+ without importing rouge-score at cloud-client import time.

### Changed: agent-learning-kit namespace
- The separate `agent-learning-kit` distribution owns `fi.alk` and all of its
  subpackages. The SDK no longer ships any `fi/alk/` file in its source tree,
  wheel or sdist; `fi.evals` and the rest of the SDK's `fi.*` API remain available.
- `fi.simulate` and `fi.opt` remain clear-error stubs pointing to
  `fi.alk.simulate` and `fi.alk.opt`. Moved evaluation names and the report module
  now name their exact `fi.alk.evals` replacements. The SDK does not import or
  install ALK, and namespace extension still supports separate install paths.

### Fixed: credential isolation
- `APIKeyAuth` no longer stores the last client's credentials on the class or its
  subclasses. Read `_fi_api_key` and `_fi_secret_key` from the client instance;
  class-level reads now return `None` with a value-free `DeprecationWarning`.
  Instance credential access and outbound authentication headers are unchanged.
- `APIKeyManager` remains process-wide and must not be used as a per-tenant store;
  credential isolation applies only to `APIKeyAuth` client instances, and manager
  deprecation is planned for 0.7.x.

### Experiment trace export
- Uploaded experiments using `trace=True` now raise `TraceExportError`
  (`TRACE_EXPORT_FAILED`, CLI exit 3) and emit one `TraceExportWarning` per run when
  an OTLP batch fails (including collector HTTP 404/405/5xx or connection failures),
  even with `progress=False`. Warning promotion never replaces the typed error or an existing
  primary failure, including interruption. Diagnostics name the endpoint and status, never
  response bodies or secrets; nonconnection request errors remain non-retryable. The error
  suggests `trace=False` (CLI `--no-trace`) for future runs without tracing. Items may already
  be stored; spans are not journaled and resume cannot recover them. Batch-processor queue
  drops and HTTP 200 OTLP partial rejections are not covered by this terminal-batch check;
  caller-owned exporters are unchanged. `futureagi-py doctor` checks `/tracer/v1/traces`
  with GET: a missing route (HTTP 404) is a setup problem; transport exceptions remain
  inconclusive ("could not check") without changing its exit code. GET responses are
  explicitly not proof that POST export works.

### Unsupported legacy helpers
- **Unsupported legacy helpers report the server limitation explicitly.**
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
  `fi.evals` or these ground-truth helpers.

### Fixed: experiments
- Discard task results that arrive at or after the trial timeout, including cancellation-suppressing async tasks and late sync tasks, without evaluating or journaling them as completed.

### Licensed operations and HTTP 402
- On `FutureAGIClient`, HTTP 402 now raises `PaymentRequiredError`; `402 LICENSE_MISSING` raises its
  `LicenseRequiredError` subclass, still catchable as `FutureAGIAPIError`. The message
  asks this server's administrator to configure an Enterprise licence, without
  claiming that hosted deployments lack the feature. Other 402 codes remain payment/
  entitlement errors and keep their server code and payload.
- Missing-licence messages name the server-reported feature when available. Tracing
  examples explain the licence requirement before calling error-feed operations;
  `help(fi.errors)` includes the error tree and legacy namespace caveat.
- Document Enterprise licensing for error-feed methods (`tracing.issues`, `issue`,
  `issue_stats` / `issueStats`) and generated feed operations. Self-hosted servers
  need a licence; cloud availability depends on the plan. Dataset user-eval methods
  document their conditional Turing/Protect model gate (`ENTITLEMENT_DENIED`, not
  `LICENSE_MISSING`); code evaluations are exempt. Generated docs use reviewed
  licensing overrides. Existing error exports are retained.
- Document the same conditional model gate on legacy `Dataset.add_evaluation`
  and `EvalTemplateManager.run_playground`, retaining their published
  `DatasetError` and `Exception` contracts, respectively.

### Console API availability errors
- Console requests returning a completely read 404 without a Console/EE API error envelope raise
  `fi.errors.ConsoleUnavailableError` (also available from `fi`), a `NotFoundError`
  subclass, in sync and async clients. The host-only diagnostic uses the failing
  response, not a preflight request. EE resource errors and `ProductNotAvailableError`
  are unchanged. Hosted Future AGI does not support Console access through the SDK
  in this release; for self-hosted Enterprise, set `FI_PLATFORM_BASE_URL` to the
  Console API origin, or check the URL when already configured. A saved-login origin
  points to the saved login, not an environment or constructor setting.
- Capped or interrupted 404 bodies do not prove Console unavailability; when the EE
  envelope cannot be parsed, retain status-only `NotFoundError` classification. This
  also applies to oversized HTML error pages, even with a `text/html` content type.

### Fixed: published compatibility
- Preserve the published 0.7.0 snake_case model fields, schemas and serialized
  names for bulk annotations and all 32 queue fields, including `by_alias=True`
  dictionary/JSON dumps and nested models. The earlier unreleased restoration of
  0.6.13 output names is superseded by the 0.7.0 contract; the archived fixture is
  unchanged. Legacy camelCase inputs and bulk read/write properties remain
  accepted with once-per-alias warnings. Extra-field and exclusion behavior stays
  native to Pydantic; request payloads are unchanged.
- `EmbeddingResponse` again accepts a released `Usage` instance as well as a
  dictionary or `EmbeddingUsage` instance. Missing completion tokens still default
  to zero, and the `EmbeddingUsage` name remains available.

## [0.7.0](https://github.com/future-agi/futureagi-sdk/compare/python-v0.6.14...python-v0.7.0) (2026-11-05)


### Features

* revamp eval template management routes and update namespace handling ([90e70a1](https://github.com/future-agi/futureagi-sdk/commit/90e70a1c800c96c3772a213035ad2412561a9659))
* **sdk:** add generated platform clients and guarded releases ([a2e781a](https://github.com/future-agi/futureagi-sdk/commit/a2e781a07d02bdb4b31c0328acd770408d2d5cd4))


### Bug Fixes

* custom eval resolution for evalId=0 and camelCase keys (TH-3610) ([866293e](https://github.com/future-agi/futureagi-sdk/commit/866293edb87362137bb2fc790f80d52a845bd3a8))
* custom eval resolution for evalId=0 and camelCase keys (TH-3610) ([7966bfa](https://github.com/future-agi/futureagi-sdk/commit/7966bfaa3ce6c7d45895f550282f9281cc40f92f))
* **datasets:** stop orphan datasets + exact by-name resolution ([1607f12](https://github.com/future-agi/futureagi-sdk/commit/1607f129bf50ba36c5120b86c0b498711b3e3d21))
* **datasets:** stop orphan datasets + exact by-name resolution (0.6.14) ([72cba35](https://github.com/future-agi/futureagi-sdk/commit/72cba3502206a3d5a114f52763c719dade4f589c))
* remove leaked credentials, restore null-safety and backward compat in dataset parsing ([8931496](https://github.com/future-agi/futureagi-sdk/commit/8931496fd3c9e0b3fe60925870e4079d8920a4a5))

### Fixed: dataset payloads (unreleased)
- `Dataset.add_run_prompt` sends `max_tokens`, `temperature`, `presence_penalty`,
  `frequency_penalty` and `top_p` under `config.run_prompt_config`, matching the
  server's readers. Model, messages, output format, concurrency, tools, tool
  choice and response format remain directly under `config`. Explicit zero
  values and supplied empty tools/response formats are retained; omitted
  optional fields stay absent. Public argument names, order, types, defaults,
  validation, column translation and return identity are unchanged. This fixes
  client payloads in the upcoming package, not a server regression or the
  immutable published 0.6.13 package.

### Fixed: published compatibility
- Restore `BulkAnnotationResponse.annotationsCreated`, `annotationsUpdated`,
  `notesCreated`, `succeededCount`, `errorsCount`, `warningsCount` as model fields,
  constructor inputs and readable/writable attributes, retaining their published
  serialization names and synchronized snake_case views. Unknown extras still
  use the existing ignore policy.
- Restore all 32 published queue input aliases while preserving snake_case fields
  and `extra='allow'`, including nested and JSON validation:
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
- Restore `fi.datasets.dataset.EvalInfoResponseHandler` and `EvalTemplate` as the
  same supported implementations exported by `fi.evals.evaluator` and
  `fi.evals.templates`, retaining their public members.
- Fix 0.6.13 compatibility: restore `fi.api.auth.DatasetNotFoundError` and
  `fi.client.HttpMethod`, `RequestConfig`, and `Routes` aliases. Restore
  `AnnotationQueue.list_queues(page_size=20)` on all public import paths; queue and
  item pagination sends `limit` without changing the 1-based `page` or defaults.
- Queue `create` displays `OMITTED_LABEL_IDS` in its Python signature instead of an
  object address.

### Changed
- List methods on `FutureAGIClient` document accepted pagination parameters and
  page-number bases. Generated tracing and integration operations no longer declare
  unsupported dialects; server-supported size aliases remain available. Free-form
  paging kwargs reach the server unchanged, with no page-base translation.
  Alert details also accept zero-based pagination for their nested log list.
- Generated prompt-label lookup methods accept the source-backed `template_id`
  and `template_name` selectors without advertising unsupported paging.
- Response compatibility: no Python runtime changes accompany the TypeScript
  catalog declaration corrections. `FutureAGIClient` preserves server success
  envelopes for enveloped alert operations, queue archive, dataset and evaluation
  deletion, and experiment deletion. Annotation labels (both aliases), alert logs,
  annotation queues/items, experiments, scores, and prompts/labels/versions retain
  their pagination envelope, including `total_pages` and `current_page`.
  Prompt-version listing always uses the server's default pagination. Bare DRF
  reads and no-content deletes are not wrapped; these type corrections do not
  change unwrapping.
- Queue `create` accepts omitted `label_ids`, with one `DeprecationWarning` saying
  they will be required. Exactly one legacy scope is used by `get_or_create_default`
  to obtain labels; that lookup can create or restore the default queue even if the
  label check then fails, but the new queue remains unscoped. If no single scope or
  no usable labels exist, `fi.queues.DefaultQueueLabelError` (a `ValueError`, also
  exported from `fi`) explains why no truthful default is available. Explicit label
  ids avoid this lookup and warning. The legacy project, dataset and agent-definition
  fields remain equally supported for default-label lookup; none scopes the new queue.
- The Python SDK installs the `futureagi-py` console script (not `futureagi`, which is the
  standalone Future AGI CLI); `python -m fi._cli` runs the same CLI. The distribution
  (`pip install futureagi`), `import fi` and the `futureagi.cli` plugin group are unchanged.
- **Ground-truth mapping setters now use atomic `PUT /model-hub/ground-truth/{id}/setup/`.**
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
- Require Python >=3.10; supported classifiers are 3.10 through 3.13.
- Declare anyio and include the fi/py.typed marker.
- Keep webhooks in futureagi; do not build or publish a separate distribution.
- Candidate wheels and source distributions include fi.gateway, the gateway
  data-plane client (`from fi.gateway import AgentCC, AsyncAgentCC`), without
  tests or bytecode, and declare typing-extensions, which it imports. Shipping
  the client is not live gateway qualification.
- Platform namespaces remain 0.x. Gateway APIs retain their
  no-breaking-change promise below 1.0.

### Deprecated
- The restored camelCase inputs and bulk response attributes remain supported.
  Prefer the corresponding snake_case field (for example `annotations_created`
  or `created_at`). Using each old alias warns once per process with a
  `DeprecationWarning` naming the new field; canonical-only construction and
  access are silent. When both inputs are present, the canonical value wins.

### Added
- Gateway `Stream` supports `with` and `AsyncStream` supports `async with` for
  chat and text completions. Exiting closes the HTTP response and discards unread
  chunks, including on early exit or a body exception, without suppressing that
  exception. `close()` / `aclose()` are idempotent. Closed streams and previously
  obtained iterators are exhausted, even for buffered SSE or cache-hit JSON;
  re-entering a closed stream does not reopen it. Closing while another thread
  or task is reading also releases the response without a generator-busy error
  or masking the context body's exception. A pending read may report a transport
  interruption; wait for that reader to finish before iterating again.

### Not in this release

- Simulation APIs are not offered in this release.

See the repository changelog for API changes.
