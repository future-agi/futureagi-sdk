# Platform SDK conventions

These rules apply to every platform namespace of `futureagi` (Python, `fi`) and `@future-agi/sdk`
(TypeScript): deployments, agent runs, agents, environments and the workspace. Each rule
names the test that enforces it. A rule without a test is a bug in this file.

## 1. One client, two origins

- One client object per mode: `FutureAGIClient` / `AsyncFutureAGIClient` (Python) and
  `FutureAGIClient` (TypeScript). Platform namespaces hang off it; there is no second client core.
- The **core origin** (`base_url`, `FI_BASE_URL`, default `https://api.futureagi.com`) serves the core
  namespaces. The **platform origin** serves the platform namespaces. It is `platform_base_url` /
  `FI_PLATFORM_BASE_URL` when set, the saved login's when the login's own keys are in use, and
  otherwise **derived** as `{base_url}/omega/api`. One `FI_BASE_URL` covers both origins.
- Selectors: `workspace_id` / `FI_WORKSPACE_ID` and `organization_id` / `FI_ORGANIZATION_ID` are sent
  as `X-Workspace-Id` / `X-Organization-Id` on platform requests. When neither is set, no selector
  header is sent and the server uses the key's own workspace.
- Self-hosted Omega EE: `platform_token` / `FI_PLATFORM_TOKEN` is sent as `Authorization: Bearer`.
  A token together with a key pair from arguments or the environment raises `MixedCredentialsError`.
- The platform origin is resolved, and its host guard run, on the **first platform call**, so a bad
  platform setting never breaks a core namespace. Constructing a client never raises.
- `client.with_options(timeout=..., retries=...)` (TypeScript: `withOptions({ timeoutMs, retries })`)
  returns a copy that shares the credentials and the connection pools. Closing a copy leaves them
  open.

Tests: `python/tests/core/test_origins.py`, `test_client_platform.py`;
`typescript/futureagi/src/_core/__tests__/origins.test.ts`.

## 2. The host guard

The key pair itself comes from **one place**: both keys as arguments, both `FI_API_KEY` /
`FI_SECRET_KEY`, or (Python) both from the saved login. With one key as an argument, the other half
is never taken from the environment, and a platform call raises `CredentialsMissingError` naming the
missing key. So "the keys' source" below is always one source for both keys, in both languages.

The keys go to the platform origin when it is **derived**, when it comes from the **same explicit
source** as the keys (both arguments, both the environment, or both the saved login), or when it is
HTTPS in the `futureagi.com` zone or HTTP(S) on loopback. Anything else raises `HostNotAllowedError`
unless `allow_custom_platform_url=True` / `FI_ALLOW_CUSTOM_PLATFORM_URL=1`
(TypeScript: `allowCustomPlatformUrl: true`) is set, which prints one stderr warning per origin.
Bearer mode is exempt. A saved login's keys are never sent to an origin from another source.
Before parsing, an origin is refused (`PlatformNotConfiguredError`, `invalid_platform_url`) if it holds
a space, a control character or a backslash, a percent sign in the host, or an IPv4 address that is
not four decimal numbers. Both languages apply the same rules and pass the same verdict table
(`tests/fixtures/platform-origins/guard-urls.json`).

No namespace follows a redirect, core or platform, in either language: a 3xx raises
`UnexpectedRedirectError`, which names the target host only, and the keys never reach another origin.
That includes a same-origin redirect (a trailing slash).

Tests: `test_origins.py`, `test_core_redirect.py`, `test_error_mapping.py::test_redirects_are_never_followed...`;
`origins.test.ts`, `core-redirect.test.ts`, `platform-base.test.ts` (redirect).

## 3. Errors: one public tree

Import errors from `fi.errors` (Python) or the package root (TypeScript). Every class is an
`SDKException`; every status class is a `FutureAGIAPIError`.

```
FutureAGIError (= SDKException)
├─ FutureAGIAPIError(status_code, payload, code, request_id, idempotency_key, retry_after)
│    ├─ BadRequestError 400
│    ├─ AuthenticationError 401 · PermissionDeniedError 403      (also AuthError)
│    ├─ PaymentRequiredError 402 → LicenseRequiredError (LICENSE_MISSING)
│    ├─ NotFoundError 404
│    │    ├─ ProductNotAvailableError (product_not_admitted)
│    │    └─ ConsoleUnavailableError (complete Console response without an API error envelope)
│    ├─ ConflictError 409 → IdempotencyKeyInProgressError · SandboxStateError
│    ├─ PayloadTooLargeError 413 (also a local refusal before sending: local=True)
│    ├─ UnprocessableEntityError 422 → IdempotencyKeyReusedError
│    ├─ RateLimitError 429 (retry_after)
│    └─ ServerError 5xx
├─ AuthError → CredentialsMissingError → MissingAuthError
├─ TransportError → APIConnectionError (possibly_applied) → APITimeoutError
├─ ConfigurationError → HostNotAllowedError · MixedCredentialsError · PlatformNotConfiguredError · ConfigurationValueError (also ValueError)
├─ UnexpectedRedirectError
├─ StreamInterruptedError (last_sequence)
└─ MissingExtraError
```

- **Status classes are shared by core and platform namespaces**, in both languages. An undeclared
  status (a 429 or 503 the spec omits) is still typed. A Console 404 with a completely read body
  and no Console/EE error envelope raises `ConsoleUnavailableError`, also a `NotFoundError`.
  Capped or interrupted reads cannot establish the absence of an envelope and do not receive
  this diagnostic. Genuine EE resource and product-not-admitted errors retain their classes.
  Hosted Future AGI does not support Console access through the SDK in this release; self-hosted
  Enterprise users should set or check the Console API origin. The failing response is the only
  evidence used, with no preflight request. Python also identifies origins from a saved login.
- `code` is the server's machine code (`idempotency_key_in_progress`) or `http_<status>`;
  `get_error_code()` (Python) is the stable SDK code the CLI's `--json` prints.
- A failure with no HTTP response raises `APIConnectionError`, or `APITimeoutError` for a timeout.
  `possibly_applied` is false only when nothing was sent. On Python core namespaces the error is
  also the exact httpx class it replaces, so `except httpx.ConnectError` keeps working.
- Platform error payloads have secret-named fields redacted, and any key the call held is scrubbed
  from the text. A body in no known error shape is classified by status (with the Console exception
  above) and never echoed.
- TypeScript core namespaces throw the same classes; the parsed body's fields are copied onto the
  error, so code that reads `e.detail` keeps working.

Tests: `python/tests/core/test_error_mapping.py`, `python/tests/test_errors.py`;
`typescript/futureagi/src/_core/__tests__/errors.test.ts`, `core-errors.test.ts`.

## 4. Retries and idempotency: three classes from the contract

| Class | Which operations | Retried on | Key |
|---|---|---|---|
| `keyed` | `x-omega-idempotent`, `durable: true` | 429, 502, 503, 504, network errors; a 409 in progress waits (`Retry-After`, else 1 s) and resends | a UUID4 minted once, or `idempotency_key=`; the same key on every attempt |
| `keyed-not-durable` | `x-omega-idempotent`, `durable: false` | 429 and errors before anything was sent | the same key |
| `http-idempotent` | not keyed; GET, HEAD, OPTIONS, PUT, DELETE | 429, 502, 503, 504, network errors | none |
| `unsafe` | not keyed; POST, PATCH | 429 and errors before anything was sent | none |

- The class comes from the generated policy table, never from a hand-written list.
- A caller's `idempotency_key` on an operation that takes none is refused before sending.
- `x-omega-not-found-on-retry-means-applied`: a 404 after an attempt that may
  have applied (a 5xx, or a connection lost after sending) is success (`already_applied`).
- `Retry-After` is honoured, in seconds or as an HTTP date, capped at 30 s per wait.
- Streams are never retried by the transport; the resumable helpers reconnect themselves.
- Every method's docstring states its retry class and idempotency contract.

Tests: `python/tests/core/test_retry_classes.py`, `python/tests/test_retry_policy.py`;
`typescript/futureagi/src/_core/__tests__/platform-base.test.ts`, `transport-retry-policy.test.ts`.

## 5. Method shapes

- Python methods take `(id, *, keyword arguments)`; TypeScript methods take `(id, options)`.
  Every TypeScript options object accepts `signal` and `timeoutMs`; stream methods take
  `idle_timeout=` / `idleTimeoutMs`.
- **Results are wire-shaped.** Python returns the generated `TypedDict` (`total=False`, open enums),
  the same plain-dict style the core namespaces return. No public annotation contains `Unset`.
  TypeScript returns the generated types.
- **Handles.** Admitted handles use the same verbs in both languages: field
  access (`.id`, `.status`; a snake_case name reads the camelCase wire key), `.data`, `.to_dict()` /
  `toJSON()`, `.refresh()`, and **one waiter, `.wait(timeout=...)`**. `create(..., wait=True)`
  mirrors the CLI's `--wait`. `wait_for_approval` is the only special-purpose waiter.
- **Cleanup.** Admitted resource handles define context-manager cleanup in Python and disposal in
  TypeScript, with an explicit cleanup method for runtimes without `Symbol.asyncDispose`.
- **Reattach.** A namespace's `get(id)` returns its handle; `client.agents.runs.get(id)` returns a `Run`.
- **Raw responses.** `client.<ns>.with_raw_response.<method>(...)` (TypeScript `.withResponse()`)
  returns the method's value as `.data` plus `request_id`, `idempotency_key`, the rate-limit headers
  and the response headers (secret values redacted). Plain results never carry them.
- **Pages.** The operations with `x-omega-pagination` return a `Page`: `.items`, `.has_more`,
  `.next_cursor`, `.next_page()`, and iteration over every item across pages (`for`, `async for`,
  TypeScript `for await`). Cursors are opaque.
- **Streams.** Resumable streams resume with `Last-Event-ID`, lose and repeat nothing, reconcile live
  deltas (`message_reset` for a regenerated message), reconnect within a bound (then
  `StreamInterruptedError(last_sequence)`), and fall back to long-poll behind a buffering proxy.
  Unknown event types are yielded, never raised.

Tests: `python/tests/core/test_surface.py`, `test_resumable.py`, `test_sse.py`;
`typescript/futureagi/src/_core/__tests__/*.test.ts`.

## 6. Module rules

1. One concern per module, 400 lines or fewer.
2. Python platform modules import only the standard library, `httpx`, `typing_extensions`,
   `fi._sdk_exception`, `fi._credentials`, `fi._http`, `fi.errors`, `fi._core.*` and
   `fi.generated.platform.*`. Never `fi.utils` or `fi.api` (another distribution overwrites them)
   and never `fi.experiments`.
3. No hand-written URL paths: every call goes through a generated policy entry, by operation name.
4. `import fi` loads no platform module; `import fi.errors` loads no `fi._core` module.
5. Each platform module is written async-first; the sync twin is generated and checked in.
6. Platform modules use a 120-column line (the credential and transport modules' width; the shared flake8 config ignores
   E501), formatted with black and isort (profile black). Other files keep their own format.

Tests: `python/tests/platform/test_gates.py`; `typescript/futureagi/src/_core/__tests__/gates.test.ts`.

## 7. Glossary

Used verbatim in docstrings and in the docs.

| Term | Meaning | Closest LangGraph / LangSmith term |
|---|---|---|
| agent | `client.agents` | assistant |
| run | `client.agents.runs`; one multi-turn conversation with an agent | thread |
| turn | `run.send()` | run |
| release | an agent version made live | — |
| deployment | a deployed project bundle with a URL | deployment |
| experiment run | `futureagi runs` / `client.experiment_runs` | experiment |
| Observe trace | — | trace |

The `Run` class docstring opens with "A run is one multi-turn conversation with an agent."
