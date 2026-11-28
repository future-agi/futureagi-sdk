# Changelog

## 0.9.0

### Upgrading from 0.8
Requests that carry your API keys are stricter in 0.9.0 in three ways:
- Plain `http://` to a Future AGI host (`futureagi.com` or one of its subdomains) is refused whatever the setting,
  `FI_ALLOW_INSECURE_HTTP=1` included, with `InsecureHttpRefusedError`. Use `https://`.
- Plain `http://` through a proxy is refused. Where plain HTTP is otherwise allowed (a loopback host or an eligible
  host with `FI_ALLOW_INSECURE_HTTP=1`), the error is `KeyedProxyRefusedError`. This applies to a proxy selected for
  the request by a caller's `requests.Session` or `FuturesSession` passed to `fi.api.auth.HttpClient`, including a
  proxy selected by the inner session that sends. A proxy configured only on a forwarding outer session does not
  cause a refusal. Use `https://` or a direct route; the session the SDK builds sends permitted plain HTTP directly.
- `fi.platform.Client`, `fi.platform.AsyncClient`, `fi.api.auth.HttpClient` and `fi.kb` uploads follow at most five
  same-origin redirects with a readable `Location` on a 301, 302, 303, 307 or 308. The scheme, host and port must
  match; an off-origin redirect raises `KeyedRedirectRefusedError`, which `fi.kb` uploads wrap in `SDKException`.
  A 300 is not followed. `HttpClient` honors a lower redirect limit on the session that sends, and its original
  request and redirect hops share the call's retry budget. Gateway clients do not follow redirects. Recognized
  keyed redirects on OTLP HTTP exporters report a failed export (`OTLP_HTTP` for an unbound collector raises the
  error from `export()`). Call the final URL directly.

Other answers are stricter in three ways:
- `health_check` requests `/healthz` and falls back to `/health` only on HTTP 404; 0.8.1 requested `/health`.
  A 3xx answer, including `304 Not Modified`, produces the `error` status rather than `ok`. Neither `health_check`
  nor `check_valid_key` follows a redirect, and `check_valid_key` returns `False` for a 3xx answer.
- A gateway base URL with no scheme (`//host:port`) needs a caller `http_client` with an absolute HTTP(S) base
  URL. The SDK checks the URL that client builds. Without such a client, pass a full `http://` or `https://`
  gateway URL to avoid `AgentCCError`.
- `fi.api.auth.HttpClient` retries connection errors and timeouts, including a timeout while reading the response
  body. A truncated body that raises `requests.exceptions.ChunkedEncodingError`, a content decoding error, or an
  unreadable redirect `Location` does not trigger a retry. 0.8.1 could repeat a request after these errors.

Code written for 0.8.1 keeps its call forms: `allow_insecure_http` on `AgentCC`, `AsyncAgentCC`, `Gateway`,
`AsyncGateway`, `fi.platform.Client`, `fi.platform.AsyncClient` and the `Prompt` class methods, and as the fourth
positional argument of `fi.api.auth.HttpClient`; the 0.8.1 field order of the gateway `RequestOptions`; and
`FI_GATEWAY_URL` or `AGENTCC_BASE_URL`, read before `FI_GATEWAY_BASE_URL`, for the gateway origin. These clients take
`True` only as the opt-in; `FutureAGIClient` and `AsyncFutureAGIClient` also take the text `"1"`. The section "Changed:
the 0.8.1 call forms are accepted" lists each form. Caller clients passed to `fi.platform` or the gateway model clients,
and sessions passed to `HttpClient`, use their own proxy routing, including `trust_env`. Exact `httpx.MockTransport`,
`httpx.WSGITransport` and `httpx.ASGITransport` answer in process on the platform and gateway model clients;
subclasses are checked as custom transports. `Prompt.delete_template_by_name` looks up the name on the 0.8.1
prompt-labels route before deleting it.

For `ExporterType.OTLP_GRPC`, install `futureagi[tracing-grpc]` or the `evals` extra on Python 3.11 and later.

### Changed: the OTLP HTTP exporters check their TLS files for an https endpoint when built
- When built for an `https://` endpoint, `OTLP_HTTP`, `FUTUREAGI`, `ARIZE`, `PHOENIX` and `LANGFUSE` raise
  `ConfigurationError` if a selected TLS file cannot be opened. The checks use `OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE`
  or `OTEL_EXPORTER_OTLP_CERTIFICATE` for the CA, `OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY` or
  `OTEL_EXPORTER_OTLP_CLIENT_KEY` for the client key, and `OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE` or
  `OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE` for the client certificate. The CA setting also accepts a directory.
  The SDK checks the explicit endpoint if given. Otherwise `FUTUREAGI` uses the traces path on `FI_BASE_URL` or its
  default base URL. `ARIZE`, `PHOENIX` and `LANGFUSE` use `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` if set, or append
  `/v1/traces` to `OTEL_EXPORTER_OTLP_ENDPOINT` if set. `OTLP_HTTP` and the vendor exporters without an endpoint use
  the local default. The error names the setting, not its value. Correct the path or unset the setting.
- For an `http://` endpoint, the SDK skips the CA certificate and client key checks when building the exporter, but
  checks the client certificate path. At export time, `requests` checks that the client key path exists when both a
  client certificate and client key are configured.
- An `OTLP_GRPC` exporter targeting `futureagi.com` or one of its subdomains refuses an `http://` target even with
  `insecure=False` or `insecure` unset, raising `fi.errors.InsecureHttpRefusedError` (a `ConfigurationError`).
  Use `https://host:port` to select TLS explicitly.

### Changed: what a keyed request is judged on
- Exporter headers given as a `dict` subclass in `ExporterConfig.headers` are read once into a plain `dict`, by name as a
  `requests` session reads them (each name, then its value through `__getitem__`). The key checks, the header pinning and
  the exporter all receive that copy, so the values judged are the values sent. A plain `dict` whose names and values are
  all plain `str` or `bytes` (or `None` values) is handed on as it is.
- A header value counts as carrying `FI_API_KEY`, `FI_SECRET_KEY` or `FI_PLATFORM_TOKEN` from the environment when the
  key appears in it in any letter case, as written or in what the value decodes to: percent escapes, hex, or standard or
  URL-safe base64 at any offset, padded or not, up to three decodings deep. This covers a Basic credential in a custom
  header or in `Proxy-Authorization` at any user length, every byte percent-encoded, and base64 of base64. Keys shorter
  than eight characters are not looked for. When one of these variables holds a value of eight characters or longer, a
  header value longer than 64 KiB counts as carrying a key without being scanned for matches. The cap is 65,536
  characters for text values and 65,536 bytes for byte values. `RequestConfig.headers` decodes valid UTF-8 byte values
  to text, so its cap is measured in characters.
  This applies to the headers a sender is handed (`default_headers`, a session's headers,
  the call's headers and `ExporterConfig.headers`); `OTEL_EXPORTER_OTLP_HEADERS` and `OTEL_EXPORTER_OTLP_TRACES_HEADERS`
  follow the narrower rule under traces below. The scan checks each value separately and applies only the decodings
  listed above. Header names are checked against credential header names, not against environment key values.
- `HttpClient` uses the class's `request` method to decide which sessions to check for headers, `auth` and cookies.
  A session using `requests.Session.request` is checked itself, even if it holds another session in `session`.
  A `FuturesSession` using its standard `request` method is checked through the session it delegates to, if it has one.
  A class that overrides `request` is checked along with the session it holds.
- `HttpClient` treats callable session `auth` and tuple subclasses as carrying credentials before preparing a request.
  For these requests, plain HTTP to a non-loopback host requires `FI_ALLOW_INSECURE_HTTP=1` where the opt-in applies;
  a proxied plain-HTTP route is refused. For a plain `(user, password)` tuple of `str` or `bytes` values, the check
  uses the prepared headers, a check that 0.8.1 also performed.
- When `Judge` uses a caller transport from `transport=`, a proxied plain-HTTP request carrying its key is refused
  before connecting. This includes loopback and other origins eligible for `FI_ALLOW_INSECURE_HTTP=1`. The transport
  check raises `KeyedProxyRefusedError`, and the judge reports an error score. The judge's own transport sends permitted
  plain HTTP directly. HTTPS requests are not refused solely because they use a proxy.
- A cloud eval registry fetch checks the borrowed client's proxy route. A keyed plain-HTTP fetch that the client
  would proxy is refused before connecting, including to loopback and to other origins eligible for
  `FI_ALLOW_INSECURE_HTTP=1`. HTTPS fetches are not subject to this proxy check; the other plain-HTTP checks
  apply to direct fetches.
- The generated `fi.generated.openapi_client.AuthenticatedClient` checks `base_url` before returning the httpx client
  it builds. It refuses to send its token over plain HTTP to a Future AGI host regardless of `FI_ALLOW_INSECURE_HTTP`,
  or to another non-loopback host without `FI_ALLOW_INSECURE_HTTP=1`. With its default transport, the generated client
  sends permitted plain HTTP directly, including to loopback, regardless of `HTTP_PROXY`, `http_proxy` or `ALL_PROXY`.
  If the SDK's proxy checks find a proxied plain-HTTP route, including one selected by `transport`, `proxy` or
  `mounts` in `httpx_args`, the client refuses it before connecting. HTTPS is not refused solely because it uses a proxy.
- The generated client sends its token in a headers dict of its own: the `headers` given to `AuthenticatedClient`, or
  shared with another client through `with_headers` or `attrs.evolve`, are left as passed, so clients built at the same
  time each send only their own token. A header in those `headers`, or in the headers given to `with_headers` on a client
  whose httpx client is already built, whose name is `auth_header_name`, `Authorization`, `Cookie`, `X-Api-Key` or
  `X-Secret-Key` in any letter case, as a `str` or a `bytes` name, is left out of the httpx client, so a header copied
  from another client (for example `dict(other.get_httpx_client().headers)`, a dict of its `.raw` pairs, or the
  `httpx.Headers` object itself) does not send that client's token, cookie or keys, and this client sends its own token
  once, under `auth_header_name`. `AuthenticatedClient` omits `Cookie`, `X-Api-Key`, `X-Secret-Key` and `Authorization`
  from `headers` and `with_headers`. If one of those is `auth_header_name`, it carries this client's token.
  Pass cookies through `cookies=`. A token header of another client under a name
  outside these (for example `X-Fi-Token`) is sent as given. On the httpx client it builds (not one passed to
  `set_httpx_client` or `set_async_httpx_client`), a request to an origin other than `base_url`'s (scheme, host or port
  differ), such as the target of a redirect followed with `follow_redirects=True`, carries none of its token header
  (`auth_header_name`, and `Authorization`), `Cookie` (a `Cookie` header and the cookies of `cookies=`), `X-Api-Key` or
  `X-Secret-Key`. The generated `Client` removes `Authorization`, `Cookie`, `X-Api-Key` and `X-Secret-Key` in the same
  way, after the caller's own `event_hooks`, on the httpx client it builds; a client passed through `set_httpx_client`
  or `set_async_httpx_client` sends as the caller built it. Assigning `event_hooks` on the httpx client either generated
  client builds (for example `client.get_httpx_client().event_hooks = {...}`) also removes this drop; to keep it, give request hooks
  through `httpx_args` `event_hooks` (they run before the drop), or append to `event_hooks["request"]` (an appended hook
  runs after the drop, so use that form for a hook that reads the request and adds no header).
- When the SDK's collector session for OTLP HTTP, Arize, Phoenix, Langfuse or Zipkin follows a redirect to a
  different origin (scheme, host or port), it keeps only `Content-Type`, `Content-Encoding`, `User-Agent`, `Accept`,
  `Accept-Charset`, `Accept-Encoding`, `Accept-Language`, `Content-Length`, `Transfer-Encoding` and `Connection`.
  Other headers from the caller or session are removed, including vendor headers, `Authorization` and `Cookie`.
  If `.netrc` is enabled, `requests` can apply credentials for the new host. A redirect that stays on the first
  origin follows the `requests` rules for cookies and the body; a redirect other than 307 or 308 can drop the body
  and its headers. For a redirect with an unreadable port in `Location`, the session raises `KeyedRedirectRefusedError`
  without sending the hop. Arize, Phoenix and Langfuse report this as a failed export.
- SDK-built `requests` sessions disable automatic redirects on keyed requests. The sessions used by `HttpClient`
  and `fi.kb` uploads return a readable same-origin 301, 302, 303, 307 or 308 to the SDK's redirect handler, which
  checks the next request before sending. These sessions raise `KeyedRedirectRefusedError` for those statuses if
  the redirect cannot be followed, or for another 3xx with a non-empty `Location`.
- When the header check treats a request as keyed solely because a value exceeds the scan limit, a refusal from that
  check starts by naming the limit: 65,536 characters for text or 65,536 bytes for a `bytes` value. The limit applies
  when `FI_API_KEY`, `FI_SECRET_KEY` or `FI_PLATFORM_TOKEN` holds at least eight characters. Keep the value within
  the limit or use an `https://` address. The note keeps the refusal's error class and code, including when
  `HttpClient` refuses a proxied request or an OTLP exporter requires an explicit endpoint. If a credential header
  or a scanned value accounts for the refusal, the note is omitted. An earlier endpoint check can refuse a request
  without scanning its headers, such as an OTLP HTTP export to a Future AGI host over plain HTTP.
- For `str` and `bytes` subclasses, exporter header normalization uses their stored content. `bytearray` and
  `memoryview` become `bytes`, `None` values are kept, and other objects are converted once with `str()`. The exporter
  and the key checks use the resulting names and values.

### Changed: credential resolution and client settings
- 0.8.1 already kept credentials on individual clients. In 0.9.0, reading `_fi_api_key` or `_fi_secret_key`
  on `APIKeyAuth` or a subclass returns `None` and emits `DeprecationWarning`; read them on the instance.
  `APIKeyManager` is a process-wide singleton with shared credentials.
- `fi.Client` and `fi.AsyncClient` (`fi.platform.Client` and `fi.platform.AsyncClient`) take the API key and secret key as
  one pair: both from `api_key=` and `secret_key=`, or, when neither argument is given, both from `FI_API_KEY` and
  `FI_SECRET_KEY`, then from the saved login when it is bound to the base URL in use (`base_url=`, else `FI_BASE_URL`,
  else `https://api.futureagi.com`). One key given without the other, or one key given with the other as an empty
  string, raises `fi.errors.MissingAuthError` before any request, and so does a missing pair; two empty strings count as
  no argument, so the pair comes from the environment or the saved login; a key from the environment does not
  complete a pair the caller started. Breaking: 0.8.1 took an omitted or empty key from the environment and
  raised `ValueError` if a key remained missing. Catch `fi.errors.AuthError` for `MissingAuthError` in 0.9.0.
- `Protect`, and the `turing` guardrail backend built on it, take the API key and secret key as one pair: both from the
  arguments, or, when neither argument is given, both from `FI_API_KEY` and `FI_SECRET_KEY`, then from the saved login
  bound to the base URL. The base URL is the argument, else `FI_BASE_URL`, else the saved login's base URL when the
  login's keys are used, else `https://api.futureagi.com`. One key given without the other, or one key given with the
  other as an empty string, raises `fi.errors.MissingAuthError` before any request, and so does a missing pair; two
  empty strings count as no argument, so the pair comes from the environment or the saved login; a key from the
  environment does not complete a pair the caller started. Breaking: the arguments win over the environment, where the
  `Protect` ported from ai-evaluation 1.1.0 sent `FI_API_KEY` and `FI_SECRET_KEY` in place of `fi_api_key` and
  `fi_secret_key`, and used `FI_BASE_URL` in place of `fi_base_url`, when those variables were set; a partial argument
  pair is not completed from the environment; and a missing or partial pair raises `MissingAuthError` (an
  `fi.errors.AuthError`) where that `Protect` raised `InvalidAuthError`; catch `fi.errors.AuthError`. `Guardrails` with
  a `turing` model raises that `MissingAuthError` from its constructor, so `except fi.errors.AuthError` catches it;
  `Guardrails` raises any `fi.errors.AuthError` it meets while building a backend as it is. An unregistered
  `GuardrailModel` raises `ValueError`; pass an enum member. An `ImportError` while loading the registered backend
  module raises `RuntimeError` that
  starts with `Failed to import backend for <model>: `, followed by the cause and an installation hint. A backend
  constructor failure other than `fi.errors.AuthError`, including an `ImportError` in the constructor, raises
  `RuntimeError` that starts with `Failed to create backend for <model>: ` followed by the cause.
- Breaking: For Langfuse configuration calls, `fi.evals.Evaluator` accepts either no Langfuse keys or a complete pair
  from one source. If either `langfuse_public_key=` or `langfuse_secret_key=` is non-empty, both arguments are required.
  Otherwise, if either `LANGFUSE_PUBLIC_KEY` or `LANGFUSE_SECRET_KEY` is non-empty, both variables are required.
  When neither source has a non-empty key, each request field is null if its environment variable is unset,
  or an empty string if that variable is set to an empty string.
  The validation source is chosen at construction; the `langfuse_public_key` and `langfuse_secret_key` attributes
  are populated separately. A valid `evaluate(..., platform="langfuse")` call with a partial pair raises
  `fi.errors.AuthError` before any request. The message ends with `Missing: <name>` and names the missing argument
  or variable. The partial pair does not prevent construction, and other calls do not add Langfuse keys from the
  instance, so `Protect` and `Guardrails` with a `turing` model also work with one `LANGFUSE_*` variable set.
  `langfuse_host` is taken from its argument, else `LANGFUSE_HOST`, apart from the key pair. Pass both Langfuse
  keys or set both variables, or unset the one you do not use.
- 0.8.1 already cached dataset configurations by base URL and keys and built a separate `Dataset` for each lookup.
  In 0.9.0, the `Dataset` name cache separates entries by default and extra headers rather than by the plain-HTTP
  opt-in. The cache stores the configuration, not the client.
- `GuardrailsGateway.with_openai`, `with_azure` and `with_local_model` keep the non-empty key, endpoint or URL on the
  gateway they build. `Guardrails` and `GuardrailsGateway` also accept per-instance `backend_options`.
  Breaking: the helpers do not set `OPENAI_API_KEY`, `AZURE_CONTENT_SAFETY_ENDPOINT`, `AZURE_CONTENT_SAFETY_KEY` or
  `VLLM_SERVER_URL`. Settings left out or passed as empty strings come from the environment. A non-empty `vllm_url`
  takes precedence over a model-specific `VLLM_<MODEL>_URL`.
- Breaking: an enabled `setup_tracing` raises `TracingAlreadyConfigured` (a `ConfigurationError`, code
  `tracing_already_configured`) when an SDK configuration is active or another global OpenTelemetry provider is set.
  To replace an SDK configuration, call `shutdown_tracing()` first. Tracers obtained through the SDK's global
  provider follow the active configuration. Tracers obtained directly from the provider returned by `setup_tracing`
  do not. If another provider is already global, configure its exporters there or set up SDK tracing before it.
- `get_exporter_preset` and `EXPORTER_PRESETS[name]` return a separate copy on each read, so headers added to one copy do
  not reach another. Breaking: `EXPORTER_PRESETS` is read-only.

### Changed: a key that reaches a request through a header follows the plain-http rules
- 0.8.1 checked the merged headers, session headers and prepared request for named key headers and Basic or Bearer
  authorization. In 0.9.0, `HttpClient` treats `X-Api-Key`, `X-Secret-Key` and `Authorization` as key headers even
  when empty. It also checks header values for `FI_API_KEY`, `FI_SECRET_KEY` or `FI_PLATFORM_TOKEN` of eight characters
  or more. A session header counts even if the call replaces it. The plain-HTTP and proxy rules apply when the check
  finds a key, and the opt-in does not allow plain HTTP to a Future AGI host.
  `HttpClient.request` passes `allow_redirects=False` to the session, with or without credentials, and handles
  same-origin redirects itself. An off-origin 301, 302, 303, 307 or 308 raises `KeyedRedirectRefusedError`. For a
  keyed request, an SDK-built session also refuses other 3xx responses with a non-empty `Location`.
- A plain `requests.Session` passed to `fi.api.auth.HttpClient` sends the request and returns its response, under the same
  routing checks as a `FuturesSession`. A keyed plain-`http://` request that the sending session would route through
  a proxy raises `KeyedProxyRefusedError` before sending. A proxy setting that does not select the request does not
  cause that refusal. 0.8.1 sent the request directly and the call with a plain session then raised `AttributeError`.
- A header value that holds the environment's `FI_API_KEY`, `FI_SECRET_KEY` or `FI_PLATFORM_TOKEN` (eight characters or
  longer) in any of the encoded forms listed above makes the request a keyed one, as the plain value does.
- The credential check reads mappings, `httpx.Headers`, lists, tuples and iterators of `(name, value)` pairs.
  0.8.1 already matched key header names case-insensitively, removed surrounding white space, read `_` as `-` and
  accepted `bytes` names. In 0.9.0 the shared check also uses these rules for exporter headers, including gRPC pairs.
- For `requests` sessions, 0.8.1 checked the prepared request with session authentication, cookies and `.netrc`
  credentials applied. In 0.9.0, `HttpClient` prepares headers without reading the upload body when `auth` is absent
  or is a plain `(user, password)` tuple of `str` or `bytes`. Auth objects and callables, including `HTTPBasicAuth`,
  `HTTPDigestAuth` and tuple subclasses, count as credentials without being called for the check; the session runs
  authentication when preparing each send attempt. A standard `FuturesSession` that delegates to another session
  uses the sending session's headers, authentication and cookies. The sending session's proxy settings decide the
  route; settings on an outer session that only forwards the call do not. Basic authorization counts as a key
  header. A `Cookie` header containing a cookie named `X-Api-Key` or `X-Secret-Key` makes the request keyed by name,
  regardless of the value. Cookie names are matched without regard to case, ignoring surrounding whitespace and
  treating `_` as `-`. Cookie values are also checked for the environment's keys.
- For response hooks and custom adapters on caller sessions, `HttpClient` checks sends on up to 16 objects with a
  callable `send` along the `session` chain. It starts at the supplied session and stops at the end of the chain,
  at a repeated object, or after the 16th such object. Deeper sends are outside this hook check.
- `FutureAGIClient` and `AsyncFutureAGIClient` take `allow_insecure_http=True` or the text `"1"` as the opt-in, as
  `FI_ALLOW_INSECURE_HTTP` does, and apply it to every management and platform call they make. `fi.api.auth.HttpClient`
  and the clients built on it, the gateway clients, `fi.platform.Client`, `fi.platform.AsyncClient` and the `Prompt`
  class methods take `True` only, as in 0.8.1: any other value given there (`"1"`, `False`, `"yes"`, a number) turns the
  opt-in off whatever `FI_ALLOW_INSECURE_HTTP` says. On every client, `False` opts out whatever the environment says and
  `None` (not given) leaves the decision to `FI_ALLOW_INSECURE_HTTP`. Prefer `https://` for hosts that are not loopback.

### Changed: the 0.8.1 call forms are accepted
- `AgentCC`, `AsyncAgentCC` (and `Gateway`, `AsyncGateway`, which pass it on), `fi.platform.Client` and
  `fi.platform.AsyncClient` accept the keyword `allow_insecure_http`, and so do the `Prompt` class methods
  `list_templates`, `delete_template_by_name`, `get_template_by_name`, `assign_label_to_template_version`,
  `remove_label_from_template_version`, `set_default_version` and `get_template_labels`, each in the position 0.8.1
  gave it. `True` opts that client or call in as `FI_ALLOW_INSECURE_HTTP=1` does; `False` opts out whatever the variable
  says. The opt-in does not extend to a Future AGI host over plain `http://`, to a plain-http request a proxy would
  carry, or to a keyed redirect to another origin: those are refused with it as without it. Copies made with
  `with_options()` keep the setting.
- `fi.api.auth.HttpClient` takes `allow_insecure_http` as its fourth positional argument, as in 0.8.1
  (`HttpClient(base_url, session, default_headers, True)`), and `extra_headers` by keyword only.
- `HttpClient.request` sends query parameters held in `RequestConfig.params` as an iterator or a generator of pairs (set
  on the config after it is built; the `RequestConfig` constructor takes a mapping): they are read once, and the same
  pairs go out on the request and on each retry.
- `HttpClient.request` retries `ConnectionError` and `Timeout` failures, including timeouts while reading the body.
  It does not retry `requests.exceptions.ChunkedEncodingError` from a truncated body, content decoding errors, or
  errors from an unreadable redirect `Location`. In 0.8.1 an unreadable `Location` could also trigger retries, up to
  the configured `retry_attempts` per call (three total attempts by default). A prompt lookup that fell back to a
  second call could send six requests.
- Gateway clients select `base_url=`, `FI_GATEWAY_URL`, `AGENTCC_BASE_URL`, then `FI_GATEWAY_BASE_URL`, in that
  order. When the SDK reads the environment and configured variables disagree, the warning names the variables
  and the selected source without printing their values.
- The gateway `RequestOptions` takes its fields in the 0.8.1 order (`method`, `url`, `body`, `headers`, `files`,
  `timeout`, `max_retries`), and `fi.gateway.resources.audio` and `fi.gateway.resources.chat.completions` expose the
  names 0.8.1 did (`RequestOptions`; for audio also `Transcription`, `Translation`, `build_extra_headers`,
  `collect_agentcc_params` and `merge_session_headers`).

- Caller httpx clients passed to `fi.platform.Client`, `fi.platform.AsyncClient`, `AgentCC` or `AsyncAgentCC`, and
  caller `requests` sessions passed to `HttpClient` or clients built on it, use their library's routing for the
  proxy check. This includes explicit proxies, mounted transports or adapters, and environment proxy settings when
  `trust_env` is enabled. With `trust_env=False`, `HTTP_PROXY` alone does not cause refusal on a direct client or
  session for an otherwise permitted destination.
- For `FuturesSession(session=inner)`, the proxy check uses the route selected by `inner`. A proxy configured only
  on an outer session that forwards the call does not cause refusal, including when the outer session overrides
  `request` to forward it. A send through the outer session itself is checked on its own route. The standard
  `requests` adapter's cached proxy managers do not determine the route; it uses a proxy selected for the request.
- Behaviour change: a caller's `FuturesSession` passed to `fi.api.auth.HttpClient` or a client built on it raises
  `KeyedProxyRefusedError` before sending a keyed plain-HTTP request if the session that sends selects a proxy.
  This includes a proxy selected from the environment with `trust_env` enabled, and a proxy selected by a
  `FuturesSession` that sends through itself. 0.8.1 sent the request directly without using the session's proxy.
  Use a session that routes directly to the destination, or an `https://` address.
- On `fi.platform.Client`, `fi.platform.AsyncClient`, `AgentCC` and `AsyncAgentCC`, a caller transport of exact type
  `httpx.MockTransport`, `httpx.WSGITransport` or `httpx.ASGITransport` answers in process without making a network
  connection or applying the plain-HTTP, opt-in and proxy checks. This includes hostnames with non-ASCII characters.
  Subclasses are checked as custom transports.
- `Prompt.delete_template_by_name` looks up the template on the 0.8.1 route, `model-hub/prompt-labels/get-by-name/`,
  with `name` as a query parameter, then deletes it.
- `fi.platform.Client`, `fi.platform.AsyncClient`, `HttpClient` and `fi.kb` uploads follow 301, 302, 303, 307 and 308
  only to the origin of the request they answer. For the platform clients that origin must also match `base_url`.
  Origins match by scheme, host and port, including an explicit default port. Each hop passes the destination and
  routing checks before sending. An off-origin redirect, including HTTPS to HTTP on the same host, is refused at
  the first hop off the origin with `KeyedRedirectRefusedError`. A 300 or a response without `Location` is not followed.
- The platform clients use `GET` for 303 and for a 301 or 302 after a `POST`. If the method changes, they drop the
  body. `HttpClient` and `fi.kb` uploads use the `requests` rules: 302 or 303 becomes `GET` except for `HEAD`, a 301
  after `POST` becomes `GET`, and 301, 302 and 303 drop the body. The redirect target supplies the query string.
  A sixth consecutive redirect raises `APIConnectionError` on the platform clients or `requests.TooManyRedirects`
  in the `requests` redirect handler. `KnowledgeBase.create_kb` and `KnowledgeBase.update_kb` wrap the latter in
  `SDKException`, as they do `KeyedRedirectRefusedError`.
- `HttpClient` respects a lower `max_redirects` on the session that sends. A followed hop uses the session's cookie
  jar and the authentication headers from the preceding request without rerunning its authentication callable.
  It replays prepared byte or text bodies on 307 and 308, including multipart bytes. The final response includes
  its redirect history, and a `Location` without a fragment carries the preceding request's fragment.
- Behaviour change: `HttpClient` shares the call's retry budget across the original request and redirect hops.
  It retries the failed hop rather than replaying the chain. 0.8.1 could follow an off-origin redirect that passed
  its checks, use the session's redirect limit (30 by default) and retry the chain. Use the final URL when possible.

### Changed: gateway base URLs the SDK cannot send to carry a code
- 0.8.1 already refused keyed plain HTTP when the gateway host was written with a non-ASCII full stop or a backslash.
  In 0.9.0, a refusal for those forms or for a plain-HTTP URL `httpx` cannot parse is an `AgentCCError`, even with
  `FI_ALLOW_INSECURE_HTTP=1`. A non-ASCII host rejected by gateway validation or a URL `httpx` cannot parse gives
  an error that is also an `httpx.InvalidURL`. The plain-transport code applies except when the URL is classified as
  a plain-HTTP Future AGI host, which gets `InsecureHttpRefusedError`. For these refusals, `health_check` reports an
  error status and `check_valid_key` returns `False` without sending; 0.8.1 raised its keyed plain-HTTP refusal.
  With `AgentCC` or `AsyncAgentCC` and a caller client using an exact in-process transport, a non-ASCII host uses
  httpx's ASCII hostname encoding for both HTTP and HTTPS, as in 0.8.1.

### Changed: a credentials URL with user info is refused
- 0.8.1 already rejects a keyed `http://` request with user info in the authority, including loopback.
  In 0.9.0, `fi.platform.Client`, `fi.evals.Evaluator` and other callers of the shared credentials URL check also
  reject user info over `https://`. This includes `user@host`, `user:password@host`, `:password@host` and
  percent-encoded user or password text. For these forms, the shared check raises `InsecureHttpRefusedError` for
  `futureagi.com` and its subdomains, or the plain-transport `ConfigurationError` for other hosts.
  `AgentCC` and `AsyncAgentCC` raise `InsecureHttpRefusedError` only for plain `http://` on a Future AGI host.
  For other URLs with user info they raise the plain-transport refusal. Management and platform calls that parse
  the unified client's origin report the platform URL validation error. The messages omit the user and password.
  Pass credentials through key options, not the URL.

### Added: sandbox exec channel, `rsh`, `ssh`, `rsync` and `scp`
- `sbx.commands.exec_stream(argv, *, stdin=None, cwd=None, env=None, timeout_seconds=None)` (and
  `AsyncSandbox`, and `client.sandboxes.commands.exec_stream(sandbox_id, argv, ...)`) runs a command
  over the sandbox's channel, a WebSocket: raw bytes in and out (NUL bytes and invalid UTF-8
  included), a separate stderr, `close_stdin()` as a half-close, `cancel()`, and `wait()` for the
  exit record. `argv` is a list the server runs without a shell. Credit-based flow control runs
  both ways (256 KiB of output, 32 KiB of stdin), so a slow reader or a slow command stops the
  other side instead of growing memory. Each connection mints its own single-use token; the socket
  sends `Origin` from the API base URL and no cookie.
- If the server closes the channel before the exit record, these close codes raise typed errors: `ChannelAccessRevokedError`
  (4401), `ChannelSandboxGoneError` (4404), `ChannelEmergencyStopError` (4409),
  `ChannelSandboxHibernatedError` (4410), `ChannelSandboxFrozenError` (4411) or
  `ChannelServerStoppingError` (1001), all `ChannelClosedError`. A 404 from the token route says the
  operator may have switched the channel off; a 409 `channel_remote_unsupported` says the sandbox
  runs on a sandbox host.
- `futureagi-py sandbox rsh SANDBOX_ID [--] COMMAND...` connects local standard input, output and
  error to the command byte for byte and returns its exit code on normal completion. `sandbox ssh
  SANDBOX_ID` opens an interactive shell. When terminal control is available and standard input is a
  terminal, the CLI uses raw input mode and restores the saved settings during cleanup. `sandbox rsync
  SANDBOX_ID ARGS...` and `sandbox scp SANDBOX_ID ARGS...` run the system `rsync` / `scp` over
  `rsh`; write the sandbox side of a path as `:path`. A missing local tool is named in the error.
- The channel disables library keepalive pings by setting `ping_interval` and `ping_timeout` to
  `None` where the connector accepts them. The blocking connector in `websockets` 16 has no
  client keepalive to disable. The server defers pongs while the client owes output credit, so a
  ping timeout could close a slow reader's connection during a transfer. If the connection drops
  before the exit record without a close frame, the stream reports a connection error.
- The data token is not in `repr`, `str` or `format` of the connection plan or of an error, and
  the plan holds it outside its fields, so `dataclasses.asdict` and `vars` do not show it. The
  channel hands `websockets` its own logger (`fi.sandbox.channel.websocket`, INFO and above, with
  any record that holds the token entry dropped), because the library logs handshake headers at
  DEBUG and `Sec-WebSocket-Protocol` carries the token. The `websockets` loggers themselves are
  left as the application set them, and DEBUG output of the channel's own connections is off.
- The channel opens over `wss://`, or over `ws://` if the channel URL itself names `localhost`, a dotted quad in
  127.0.0.0/8, or `::1`. The API URL's scheme does not affect this check. The SDK checks the URL and offered
  protocols before opening a socket: a nonempty query, fragment or user information, a non-ASCII host, or an offer
  missing the channel subprotocol or token is refused. On loopback the channel handshake goes directly over
  `ws://` or `wss://`. The token request and other loopback calls made by the default `FutureAGIClient` and
  `AsyncFutureAGIClient` platform transports also bypass environment proxies.
- The WebSocket handshake does not follow a redirect, so the token goes only to the address the
  server named. The token is not in the locals of the frames of the errors this SDK raises for a
  refused reply, a refused upgrade or a redirect (frames inside the WebSocket library are not
  covered), and the server's text in a stream error, a close reason or a refused upgrade is
  stripped of control characters (C0 and C1), bidirectional overrides and zero-width characters, then
  scrubbed of it, then cut to 200 characters, so a token split by one of those characters is
  removed. `rsync` and `scp` run this CLI again as their
  remote shell: the `futureagi-py` console script when that is the program running, else `python -I -m fi._cli`, so the
  re-run does not import from the current directory.

### Changed: channel ports and the websockets requirement
- A channel URL whose port is 0, above 65535, or not 1 to 5 ASCII digits (a sign, a space, an underscore,
  non-ASCII digits, an empty port after the colon) is refused with `ChannelProtocolError` before any socket
  opens. The port is read from the URL as written, so `wss://host:/c`, `wss://host:80<newline>/c` and
  `wss://host:8<tab>0/c` are refused too. Use a port from 1 to 65535 written with 1 to 5 ASCII digits, or omit it.
- `futureagi` installs `websockets` 16 or 17 (`>=16.0,<18`). With a websockets version whose blocking connect has
  the redirecting class but not the `process_redirect` hook, the first use of the sync channel raises an
  `ImportError` that ends with "install websockets 16.x or 17.1 and later below 18"; install one of those
  versions. `import fi.sandbox` and the async client do not load the sync channel module, so they do not raise it.

### Changed: platform proxy routing
- In 0.8.1, `fi.platform` already uses httpx's environment proxy routing for HTTPS and sends plain HTTP directly.
- The default `FutureAGIClient` and `AsyncFutureAGIClient` platform transports send loopback requests and keyed plain
  HTTP directly. Other requests use httpx's `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY` routing. For
  loopback HTTPS, `fi.platform.Client` and `fi.platform.AsyncClient` use httpx's environment proxy rules; an
  applicable proxy carries a `CONNECT` tunnel. Proxy URL credentials are sent to the proxy as `Proxy-Authorization`.
  The `FutureAGIClient` and `AsyncFutureAGIClient` transports record each attempt's outcome to help distinguish
  whether an operation may have been applied.

### Changed: loopback calls, server text and the channel URL
- The shared Python loopback check recognizes the same hosts as the 0.8.1 plain-HTTP rule: the exact name
  `localhost` (any case), an address in 127.0.0.0/8, or `::1`. A trailing dot, a short or alternate IPv4 spelling,
  or an IPv6 zone identifier does not qualify. Individual URL validators may reject those forms outright. Use
  `localhost`, a canonical loopback IPv4 address, or `[::1]` in a URL. The OTLP gRPC plain-channel check also
  recognizes bracketed IPv4-mapped loopback addresses such as `[::ffff:127.0.0.1]`.
- Direct `localhost` connections in the default `FutureAGIClient` and `AsyncFutureAGIClient` transports, the gateway
  clients and the sandbox channel try `127.0.0.1` first, then `::1` if the first address cannot be reached. They
  bypass the system resolver and preserve the URL host for the handshake and certificate check. `fi.platform`
  retains standard httpx routing for HTTPS. A different hostname that resolves to loopback is subject to the usual
  proxy rules; an applicable HTTPS proxy is used via `CONNECT`.
- Under the shared origin policy, guarded credential-bearing requests can use plain HTTP to loopback. A remote
  destination requires an explicit opt-in and must pass its destination and proxy checks. The opt-in does not apply
  to `futureagi.com` or its subdomains. A percent-encoded host is refused by the shared plain-HTTP URL check even
  with the opt-in. The shared check uses `ConfigurationError` for an origin refusal; gateway clients use
  `AgentCCError`. `health_check` reports an error status and `check_valid_key` returns `False` on a refused origin.
- When a guarded plain-HTTP route fails the proxy check, the SDK raises `KeyedProxyRefusedError`
  (`KEYED_PROXY_REFUSED`). `fi.gateway.openai_kwargs` checks environment proxy routing. A generated
  `AuthenticatedClient` checks the route when it builds its underlying client, including proxy options in
  `httpx_args`. Its default transport sends plain HTTP to loopback directly. A remote plain-HTTP route requires the
  opt-in and must not be selected by an environment proxy. Use HTTPS, or for an otherwise permitted plain-HTTP
  destination use a direct route, with `NO_PROXY` where applicable.
- The shared plain-HTTP check writes one opt-in notice per process to standard error, naming
  `FI_ALLOW_INSECURE_HTTP` and the origin without a path or credential. The separate OTLP plain-transport check
  can also log a `WARNING` once per process via `fi._otlp_headers`, naming the setting without the host.
- In 0.8.1, the SDK-built gateway transports and the gateway utilities already sent permitted keyed plain HTTP
  directly. In 0.9.0, the SDK-built transports for `AgentCC`, `AsyncAgentCC`, `health_check`, `check_valid_key` and
  experiment trace export also bypass environment proxies for loopback HTTPS. Remote HTTPS routes retain environment
  proxy settings. The gateway utilities use `httpx.get` or `httpx.post` for remote HTTPS and the gateway's direct
  client for loopback or plain HTTP. Test replacements for those functions are called for every allowed destination.
- The OpenTelemetry exporters of `fi.evals` (OTLP over gRPC and HTTP, Arize, Phoenix, Langfuse, Future AGI and
  Zipkin) send an export to a loopback collector straight to this machine: the HTTP exporters use a session that
  skips the proxy for a loopback request, and the gRPC exporter sets `grpc.enable_http_proxy` to 0 for a
  loopback endpoint. A collector on another host keeps the proxy, except for a plain export that carries keys (an
  `http://` endpoint, or a gRPC channel without TLS), which connects straight to the collector.
- `health_check` and `check_valid_key` retain `SSL_CERT_FILE` and `SSL_CERT_DIR` when bypassing an environment proxy,
  so loopback HTTPS can use a locally configured CA. The legacy `fi.api` and knowledge-base `requests` paths continue
  to support `.netrc`, as in 0.8.1. The evaluation registry's `requests` path also supports it. The httpx gateway
  clients and utilities do not read `.netrc`; pass credentials as arguments or environment variables.
- Gateway clients already declined redirects in 0.8.1, with an `APIStatusError`. In 0.9.0, a 3xx response raises an
  error that is both an `APIConnectionError` and a `KeyedRedirectRefusedError` (`get_error_code()` is
  `KEYED_REDIRECT_REFUSED`, `status_code` is set, and `target_host` is `None`). The message omits `Location` and the
  target. Sync, async and streaming calls do not follow or retry the redirect; `health_check` reports `error` for a
  3xx response. Set the base URL to the final address.
- `health_check` sends `GET /healthz` and tries `GET /health` only if that returns HTTP 404. In 0.8.1 it sent
  `GET /health` directly.
- The channel's server text (a stream error, a close reason, a refused upgrade) drops every control and format
  character (Unicode Cc and Cf), every surrogate code point, every Default_Ignorable_Code_Point (the Hangul
  fillers, the variation selectors, the combining grapheme joiner and the unassigned ignorable ranges), the line
  and paragraph separators, the braille blank (U+2800) and the musical symbol null notehead (U+1D159) before the
  token is looked for. A space separator (Unicode Zs) is removed only inside a span that holds the token, and
  every other space of the text stays, including the spaces between two spans. The Python SDK uses a code-point
  table rather than the Python interpreter's Unicode data.

### Changed: scope of the plain-HTTP opt-in
- 0.8.1 already required an explicit opt-in for keyed plain HTTP to a non-loopback host. In 0.9.0 the policy also
  covers platform and management calls from `FutureAGIClient` and `AsyncFutureAGIClient`, the evaluation registry,
  experiment trace export and credential-bearing OTLP export, including eligible gRPC channels without TLS. Use
  HTTPS, or set `FI_ALLOW_INSECURE_HTTP=1` for an eligible destination on a trusted network. Only the exact value
  `1` opts in. The two clients also accept `allow_insecure_http=True`; passing `False` disables the environment
  opt-in. Destination and proxy checks apply as well.
- Sandbox calls (`client.sandboxes` and `fi.sandbox`, including file downloads) require HTTPS or loopback. A
  non-loopback HTTP origin is refused with `insecure_sandbox_origin` even with `FI_ALLOW_INSECURE_HTTP=1`, regardless
  of proxy settings. Loopback HTTP is permitted.

### Changed: direct sends over plain HTTP and destination checks
- 0.8.1 sends permitted keyed plain HTTP directly on SDK-built gateway, platform and `fi.api` paths. In 0.9.0
  the transports and sessions for plain HTTP that the SDK sends itself read no `HTTP_PROXY`, `HTTPS_PROXY` or `ALL_PROXY`
  on the keyed paths listed above, including the management calls of `FutureAGIClient` and `AsyncFutureAGIClient`.
  A plain gRPC exporter channel carrying recognized credentials sets `grpc.enable_http_proxy=0`. For a permitted
  direct send, `NO_PROXY` does not affect the route. Use an `https://` address if the request needs a proxy.
- The shared credential URL check refuses plain `http://` text with surrounding whitespace or control characters
  with a `ConfigurationError` instead of sending to a URL normalized by an HTTP library. Some clients validate
  the URL before this check; experiment collector validation, for example, reports `ExperimentError`.
- Breaking: 0.7.1 shipped `KeyedProxyRefusedError` on a separate release line. The published 0.8.1 also checks
  adapters for keyed plain HTTP and inspects wrapped `requests` sessions. In 0.9.0, the platform and gateway model
  clients check the transport selected by a supplied httpx client. `HttpClient` checks the sending `requests`
  session's proxy route and adapter, including the inner session of a `FuturesSession` and requests to loopback.
  These callers use the sending library's routing, including environment proxies when `trust_env` is enabled. Other
  callers use the shared environment check where applicable. A route that counts as proxied for an otherwise
  permitted keyed plain-HTTP request raises `KeyedProxyRefusedError` (also a `ConfigurationError`) before sending.
  A plain URL with user info is refused for its user info regardless of proxies. Send with a direct client or let
  the SDK build the transport.
- Breaking: 0.7.1 shipped keyed redirect refusal for `HttpClient` and `fi.kb` uploads on a separate release line.
  Published 0.8.1 follows permitted redirects on `fi.api` paths and same-origin redirects for `fi.platform`.
  In 0.9.0, `fi.platform.Client`, `fi.platform.AsyncClient`, `HttpClient` and `fi.kb` uploads follow the supported
  redirect statuses only on the original origin. The redirect handlers raise `KeyedRedirectRefusedError` for a
  redirect to another origin. `fi.kb` uploads wrap the error in `SDKException`; in 0.8.1 they could follow a
  permitted off-origin redirect. Gateway clients decline all 3xx responses with a subclass of
  `KeyedRedirectRefusedError`.
  `UnexpectedRedirectError` names the same base class, which is not a `requests.RequestException`.
  `Evaluator.evaluate` reports a refused evaluation redirect as a failed result with the error message. A
  configuration request sent by `Evaluator.evaluate(..., platform=...)` raises the error.
  An unreadable `Location` does not trigger a retry on `HttpClient`, `APIKeyAuth` or SDK-built HTTP OTLP sessions.
  This also applies when a caller's `requests` session raises a decoding error while reading `Location`.
  A generated `AuthenticatedClient` does not follow redirects by default. When the HTTP client it builds follows
  redirects, it removes the configured token header, `Authorization`, `Cookie`, `X-Api-Key` and `X-Secret-Key` on a
  hop to another origin. A same-origin hop can retain them. A client passed to `set_httpx_client()` or
  `set_async_httpx_client()` sends as the caller built it.
  The redirect errors from `FutureAGIClient` and `AsyncFutureAGIClient` report the target host when `Location`
  can be resolved. Gateway, `fi.platform` and SDK-built `requests` session refusals report `status_code` without
  naming the target. When `HttpClient` handles the response itself, its refusal carries `target_host` if `Location`
  supplies a readable hostname, including in a scheme-relative URL. For recognized credentials, Arize, Phoenix,
  Langfuse and Future AGI report a refused redirect as a failed export; `OTLP_HTTP` for an unbound collector raises
  `KeyedRedirectRefusedError` from `export()`. If a request follows a redirect, the SDK-built session drops vendor
  headers such as `api_key` on a hop to another origin; a same-origin hop can retain them. Set the base URL to the
  final address.
- 0.8.1 refuses keyed plain HTTP to hosts written with non-ASCII dots. In 0.9.0, the shared plain-HTTP check does
  not count an address written with an ideographic, fullwidth or halfwidth full stop as loopback. The `fi.platform`
  clients refuse such plain-HTTP base URLs at construction. Gateway clients refuse them on network sends even with
  `FI_ALLOW_INSECURE_HTTP=1`. The sandbox client refuses that spelling in `OMEGA_BASE_URL` for HTTP and HTTPS,
  with `invalid_base_url`. Use ASCII dots for loopback addresses.
- Breaking: `OTLP_HTTP`, `OTLP_GRPC`, Arize, Phoenix and Langfuse raise `ConfigurationError` when their `headers=`
  carry keys and no endpoint is supplied. Set the endpoint to your collector. With no endpoint, `FUTUREAGI` uses
  `FI_BASE_URL` or the default Future AGI base URL.
- The `FUTUREAGI` exporter sends its configured or SDK headers rather than OTLP environment headers. If either
  `OTEL_EXPORTER_OTLP_HEADERS` or `OTEL_EXPORTER_OTLP_TRACES_HEADERS` carries a recognized Future AGI credential,
  the environment check refuses a destination outside `futureagi.com` and its subdomains, even if the destination
  is configured by `FI_BASE_URL`, `FI_TRACES_URL` or `FI_GRPC_URL`. For Arize, Phoenix and Langfuse, this check
  runs before an endpoint supplied only through the OTLP endpoint settings is resolved. For Future AGI destinations
  it applies the plain-transport rule to HTTP and scheme-less gRPC; gRPC also checks the channel's transport.
  The error names the setting without printing its value. The environment check recognizes `x-api-key`,
  `x-secret-key` and supported text forms of the SDK's keys, but does not cover all credential values. Use `headers=`
  for the broader credential checks and TLS for collectors that receive credentials.
- The evaluation template registry sends its request with redirects off. A 3xx answer gives no templates: the registry logs a
  warning that names the URL and the error type and returns an empty registry; it does not raise.
- Breaking: the shared credential check refuses plain HTTP to `futureagi.com` and its subdomains even with
  `FI_ALLOW_INSECURE_HTTP=1`. The check uses the normalized connection host. It raises `InsecureHttpRefusedError`
  (also a `ConfigurationError`, available from `fi`, `fi.errors` and `fi.utils.errors`). Gateway clients also use
  this error for a readable Future AGI host in a plain-HTTP base URL with user info. Gateway helpers report their
  failure values instead of raising. The HTTP exporters (`OTLP_HTTP`, `FUTUREAGI`, Arize, Phoenix and Langfuse)
  refuse a plain-HTTP Future AGI endpoint at construction; an invalid endpoint can fail a separate validation.
  Experiments apply the credential check while setting up tracing, before creating the exporter or sending spans.
  An explicit plain-HTTP `FI_COLLECTOR_ENDPOINT` that is neither loopback nor on the same host as a plain-HTTP API
  base fails endpoint validation with `ExperimentError` first. Use an `https://` address for Future AGI.
- The shared credential URL check refuses an empty host, backslashes in the authority and user info in HTTP
  and HTTPS URLs, including percent-encoded backslashes and brackets in user info. For plain HTTP it also refuses
  an `@` after the authority. The shared check does not count nonstandard IPv4 spellings as loopback; individual
  clients can also reject a URL that their parser cannot read.

- For an unbound OTLP gRPC collector, `https://` selects TLS regardless of `insecure`. For other endpoints, the
  exporter uses an explicit `insecure` value. With `insecure=None` it uses `OTEL_EXPORTER_OTLP_TRACES_INSECURE`,
  then `OTEL_EXPORTER_OTLP_INSECURE`, then whether the endpoint starts with `http://`. A loopback target bound by
  `FI_BASE_URL`, `FI_TRACES_URL` or `FI_GRPC_URL` uses TLS and refuses `insecure=True`.
  A plain channel for recognized credentials to a Future AGI host raises `InsecureHttpRefusedError`; another
  non-loopback host requires `FI_ALLOW_INSECURE_HTTP=1`. With credential-bearing `headers=`, the check also
  requires the opt-in for a non-loopback `http://` endpoint when `insecure=False` selects TLS. The opt-in does
  not make an ambiguous or empty authority valid. A `dns:///` target is refused when `headers=` carry credentials;
  a bound `dns:///` target can use TLS with the headers the SDK supplies.
  The plain gRPC check reads a bracketed IPv6 host as an address. It treats `::1` and IPv4-mapped addresses in
  `::ffff:127.0.0.0/104` as loopback and refuses a plain endpoint with a zone ID. HTTP senders do not treat
  IPv4-mapped IPv6 addresses as loopback. The gRPC `headers=` check recognizes `x-api-key`, `x-secret-key`,
  `authorization` and supported forms of SDK key values. When a configured SDK key has at least eight characters,
  a header value above 64 KiB is treated as credential-bearing without scanning the value.
- The Python conformance tests use `tests/experiments/unit/fixtures/plaintext-rule-oracle.json.gz` in the Python
  source tree to compare applicable OTLP HTTP, OTLP gRPC and evaluation configuration cases. For measured routes,
  the tests count synthetic credential bytes at loopback listeners.

### Changed: redirect handling and direct sends by client
- The Future AGI, Arize, Phoenix and Langfuse OTLP HTTP exporters do not follow redirects on recognized keyed
  requests. A 301, 302, 303, 307 or 308 response fails the batch with or without `Location`; another 3xx response
  fails it when `Location` is non-empty. Experiment trace export does not follow redirects, records the HTTP
  status and treats a non-2xx response as a failed export.
- On the platform and gateway model clients, exact `httpx.MockTransport`, `httpx.ASGITransport` and
  `httpx.WSGITransport` answer in process without the plain-HTTP or proxy checks, as in 0.8.1. Subclasses are
  checked as custom transports. For network calls, an exact `HTTPTransport` or `AsyncHTTPTransport` can use a
  direct pool. A wrapper without a pool counts as direct if the SDK finds at least one delegate and every delegate
  counts as direct. The check reads instance attributes and slots, including transports held in containers or by
  embedded httpx clients. An `HTTPTransport` or `AsyncHTTPTransport` subclass with a pool, an uninspectable
  transport, or a transport that would proxy the request triggers `KeyedProxyRefusedError` on an otherwise
  permitted keyed plain-HTTP request, including to loopback. Use an exact `HTTPTransport` or `AsyncHTTPTransport`
  for network calls, or `httpx.MockTransport` or `create_mock_client()` in tests.
- 0.8.1 sends permitted keyed plain HTTP directly for SDK-built gateway clients, `check_valid_key` and `health_check`.
  In 0.9.0, a plain-HTTP `health_check` without a key also goes directly. Neither follows a redirect: `health_check`
  reports `error` for any 3xx response, a `304 Not Modified` included, where 0.8.1 reported `ok`, and `check_valid_key`
  returns `False` for it.
- 0.8.1 sends permitted keyed `fi.kb` uploads directly over plain HTTP. In 0.9.0 the evaluation template registry
  also sends permitted keyed plain HTTP directly when it builds its own session. As with uploads, that session
  keeps the CA bundle setting and uses environment proxies for HTTPS to non-loopback hosts as configured.
  HTTPS to loopback goes directly on these SDK-built sessions.

### Changed: gateway destinations the SDK refuses
- With a caller `http_client` that has an absolute HTTP(S) `base_url`, `AgentCC`, `AsyncAgentCC`, `Gateway` and
  `AsyncGateway` accept a gateway base URL with no scheme (`//host:port`). The request uses the caller client's
  origin and path prefix, rather than the host after `//`. The SDK checks the resulting URL and the caller's
  route before sending. On a network route, plain HTTP to a Future AGI host is refused, other non-loopback hosts
  require opt-in, and plain HTTP through a proxy is refused. Without a caller client with an absolute HTTP(S)
  `base_url`, the SDK raises `AgentCCError` before sending. Supply a full `http://` or `https://` gateway URL.
- `check_valid_key` returns `False` without sending the key to these destinations: plain `http://` to a Future AGI host,
  plain `http://` to a host that is not loopback without `FI_ALLOW_INSECURE_HTTP=1`, or a base URL with user info.
  `health_check` returns the `error` status for the same destinations when it has a gateway key; with no key it sends
  to a plain `http://` host and reports that host's answer, and a base URL with user info gives `error`. Neither raises
  for them.
- A gateway client called with a base URL that httpx cannot read (an octal address such as `0177.0.0.1`, or a host name
  httpx cannot encode) sends nothing, whether or not `FI_ALLOW_INSECURE_HTTP=1` is set. For an `https://` URL whose host httpx
  cannot read it raises httpx's own `httpx.InvalidURL` (a port that cannot be read raises `AgentCCError` first); for an `http://` URL it raises the SDK's refusal, an `AgentCCError` that is also an
  `httpx.InvalidURL` (see gateway base URLs above), so `except httpx.InvalidURL` catches both.
- Breaking: 0.8.1 refuses user info in keyed plain-HTTP URLs. In 0.9.0, gateway clients and helpers refuse a
  base URL with user info on HTTP or HTTPS. The shared credential check also refuses user info on keyed HTTPS
  requests from `fi.evals.Evaluator` and clients built on `HttpClient`, including datasets and knowledge bases.
  Remove user info from the base URL and supply credentials through the client's authentication options.
- 0.8.1 refuses keyed plain HTTP to a host written with non-ASCII characters even with the opt-in. In 0.9.0, for a
  plain-HTTP host such as `api.ｆutureagi.com` that httpx cannot encode, `HttpClient` and `fi.kb` report
  `ConfigurationError` without the opt-in. With `FI_ALLOW_INSECURE_HTTP=1`, `HttpClient` reports
  `requests.exceptions.InvalidURL`, `create_kb(...)` wraps that error in `SDKException`, and a lookup in the
  constructor reports the named knowledge base as not found. No request is sent. Write the host in ASCII and use
  `https://`.

### Changed: plain-HTTP opt-in with a proxy, the proxy rule and channel ports
- 0.8.1 already checked supplied httpx clients for proxies and rejected keyed plain-HTTP requests through custom
  `requests` adapters. In 0.9.0, a route that counts as proxied raises `KeyedProxyRefusedError` (a
  `ConfigurationError`) for otherwise permitted keyed plain HTTP. This includes loopback and applies with
  `FI_ALLOW_INSECURE_HTTP=1` or `allow_insecure_http=True` where accepted. Use `https://` or send directly.
  The SDK checks the httpx transport selected for the request, including `proxy=` and `mounts=`. `HttpClient`
  checks the sending session's applicable proxy settings and adapter. An uninspectable httpx transport or route
  counts as proxied, as does a custom `requests` adapter. A wrapper without a pool counts as direct if it holds at
  least one transport and all of its delegates count as direct, including delegates held in slots. Exact
  `httpx.MockTransport`, `httpx.ASGITransport` and `httpx.WSGITransport` bypass the check on the platform and
  gateway model clients. With `LazyKeyAuth`, exact `httpx.MockTransport` counts as direct and the built-in
  `httpx.ASGITransport` and `httpx.WSGITransport` count as proxied.
- The stack walk that finds the `httpx` client sending a `LazyKeyAuth` request has no depth limit. When the
  request has no client on the stack, a plain-HTTP request counts as proxied, a loopback host included, so a request
  that carries keys to `http://127.0.0.1` raises `KeyedProxyRefusedError`.
- The shared environment proxy check applies on some paths, including `openai_kwargs()` and non-loopback plain
  HTTP on `LazyKeyAuth`. Where it applies, a request counts as proxied if the CPython-style check, httpx or
  `requests` selects a proxy, or if a router raises an error. For example, httpx does not match the bare host
  `example.com` against `.example.com`, so this check can refuse an opted-in request even when `requests` would
  bypass the proxy. List the bare host in `NO_PROXY` as `example.com`, or unset the proxy variable. Caller clients
  and sessions passed to `fi.platform.Client`, `fi.platform.AsyncClient`, `AgentCC`, `AsyncAgentCC` or
  `fi.api.auth.HttpClient` use their sending library's routing rather than the shared environment check, for
  both loopback and other hosts.
- The SDK's CPython-style check considers non-empty `HTTP_PROXY` and `ALL_PROXY` in any letter case;
  `HTTPS_PROXY` alone does not select a proxy for plain HTTP. For `NO_PROXY`, a non-empty variable in any letter
  case sets the value; names ending in lower-case `_proxy` take precedence, and an empty one clears it.
  The whole value `*` matches every host. Otherwise, the check trims each comma-separated entry, strips leading
  dots and compares without regard to case. It matches the host or `host:port` in full or at a dot boundary from
  the end. It keeps trailing dots and, when given the original URL text, compares port digits as written (`:08`
  and `:8` differ). In a list or name, `*` is literal. This check does not match CIDR ranges; the sending library
  may interpret some entries differently.
  If `ALL_PROXY` set to a non-empty value routes an `http://` request through a client or session you pass in,
  the opt-in does not permit that send. Unset `ALL_PROXY` or add a matching `NO_PROXY` entry. The SDK's own
  direct-send paths do not use `ALL_PROXY` for plain HTTP.
- 0.8.1 already refused keyed plain-HTTP URLs with no host or a backslash or percent encoding in the authority.
  The shared credential check in 0.9.0 also refuses a plain-HTTP URL with an `@` after the authority, including
  on loopback. Use a URL with one unambiguous host and no backslash in the authority. For plain HTTP, keep `@`
  out of the path, query and fragment.
- 0.8.1 already checked credentials from a `requests` session's own headers and authentication. In 0.9.0,
  `HttpClient` treats a session's `X-Api-Key`, `X-Secret-Key` or `Authorization` header as a credential by name,
  even if the call supplies none. It checks headers added by session authentication and treats callable session
  authentication as credential-bearing without running it for the check.
- A channel URL port is 1 to 5 ASCII digits naming 1 to 65535 and is read as a decimal number, so `:08` is port 8
  and `:00080` is port 80. A port written with six or more digits is refused.

### Changed: error codes for refused requests
- Gateway model clients raise `AgentCCError` for destination refusals. The coded refusals expose the same value
  through `.code` and `get_error_code()`. If a supplied `http_client` may proxy an otherwise permitted plain-HTTP
  request, the gateway model clients raise `KeyedProxyRefusedError` instead of `AgentCCError`.
  `KnowledgeBase(kb_name=...)` propagates `ConfigurationError` from the lookup; 0.8.1 already propagated the
  plain-HTTP `ValueError`. The evaluation template registry propagates `ConfigurationError`; after a 3xx response,
  it logs a warning and returns an empty registry. OTLP exporters use the code of the
  [plain-transport rule](#changed-traces-to-future-agi) for an ambiguous authority.
- `host_not_allowed` (`HostNotAllowedError`): a separately configured platform origin comes from a different source
  than the keys and is neither loopback nor HTTPS in the Future AGI zone. Pass `allow_custom_platform_url=True` or
  set `FI_ALLOW_CUSTOM_PLATFORM_URL=1` for an origin you trust. The plain-HTTP transport rule applies as well.
- `invalid_platform_url` (`PlatformNotConfiguredError`): `FI_PLATFORM_BASE_URL` is not an absolute `http://` or
  `https://` URL with a host; holds a user name, a query, a fragment, a space, a control character or a backslash;
  percent-encodes its host; or writes an IPv4 address other than as four decimal numbers with ASCII dots. Set it to a
  plain origin. A plain `http://` origin that is not loopback passes this check and meets the host rule above and the
  plain-http rule when a call sends keys to it.
- `custom_base_url_not_allowed`: the sandbox connection refuses keys to an HTTPS host outside the Future AGI zone
  and loopback, or refuses a self-host Bearer token to an HTTPS host outside loopback. For keys with `OMEGA_BASE_URL`,
  set `FI_ALLOW_CUSTOM_PLATFORM_URL=1` for a host you trust. With an explicit CLI `--base-url`, use
  `--allow-custom-base-url` instead. `FutureAGIClient.sandboxes` applies the platform origin rule to keys.
  To send a self-host Bearer token to a trusted HTTPS host outside loopback, pass `allow_custom_base_url=True` to
  `FutureAGIClient` or use `--allow-custom-base-url` on the command line; the environment setting does not permit it.
- `missing_base_url`: the sandbox has no base URL. Set `OMEGA_BASE_URL`, or pass the base URL to `FutureAGIClient`.
- Gateway model clients and `fi.platform.Client` refuse keyed plain-HTTP requests with an empty host, user info,
  brackets in user info, a backslash in the authority, or an `@` after the authority, even with the opt-in. The
  refusal normally uses the code of the [plain-transport rule](#changed-traces-to-future-agi).
  `fi.platform.Client` and `fi.platform.AsyncClient` also check the plain-HTTP base URL at construction for a
  backslash anywhere or an ideographic, fullwidth or halfwidth full stop in the host. They raise
  `InsecureHttpRefusedError` if httpx identifies a Future AGI host, and `ConfigurationError` with the code of the
  plain-transport rule otherwise. Gateway model clients refuse such full stops in a plain-HTTP host on network
  sends. For a plain-HTTP URL with a backslash only in its path that httpx can parse, they raise `AgentCCError` without a
  refusal code for other hosts, and `InsecureHttpRefusedError` for Future AGI hosts.
  With user info and a Future AGI host, the platform clients raise `InsecureHttpRefusedError` over HTTP or HTTPS.
  Gateway model clients use that class over HTTP and the plain-transport code over HTTPS. Gateway management
  (`client.gateway`) reports user info in its base URL as `PlatformNotConfiguredError` with the platform URL code.
  For refused destinations, `health_check` reports `error` and `check_valid_key` returns `False` rather than
  sending a request. A keyless `health_check` can send with an `@` in the path of a plain-HTTP base URL.
  The plain-transport refusal reports the same value through `.code` and `get_error_code()`;
  `HostNotAllowedError` and `PlatformNotConfiguredError` use their class-specific `get_error_code()` values.
- `openai_kwargs()` builds arguments for an OpenAI client you create. The default client reads the proxy
  environment itself. The helper checks the gateway destination first, then raises `KeyedProxyRefusedError` if
  an otherwise permitted plain-HTTP URL, including loopback, is judged to use an environment proxy. Use an
  `https://` URL or a `NO_PROXY` entry that the applicable routers match.

### Changed: traces to Future AGI
- The SDK-built OTLP exporters for Future AGI send configured headers or SDK credentials, plus transport headers.
  They omit headers from `OTEL_EXPORTER_OTLP_HEADERS` and `OTEL_EXPORTER_OTLP_TRACES_HEADERS`. If the SDK cannot
  set the headers, the evals tracer raises `fi.errors.ConfigurationError` (code `unsupported_otlp_exporter`).
  An experiments run records a trace export failure, continues storing items, and reports the failure at shutdown
  (CLI exit code 3). To use permitted OpenTelemetry headers with your own collector, select a non-`FUTUREAGI`
  evals exporter and set its endpoint to that collector. The OTLP exporter dependencies are limited to the tested
  range, `>=1.39.1,<1.46`, for HTTP and gRPC alike.
- The evals tracer's HTTP exporter for Future AGI uses an SDK session. It skips
  `OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER` and netrc, including on a followed redirect, while
  respecting applicable proxy and certificate settings. With credentials, it does not follow redirects and reports
  failure for HTTP 301, 302, 303, 307, 308, or another 3xx with a non-empty `Location`, even if `Location` is
  unreadable. Other 3xx responses, such as 304 without `Location`, can count as successful. Without credentials it
  can follow a readable redirect, and a hop to another origin keeps only the request headers listed for an SDK-built
  `requests` session under what a keyed request is judged on. The SDK-built experiments exporter also skips the
  credential provider and netrc, but follows no redirects and treats every non-2xx response as a failure.
  HTTP exporters use Requests' proxy settings for non-loopback HTTPS destinations; HTTPS loopback requests go direct.
  gRPC uses its own proxy settings. For TLS targets written as `host:port` or `https://host:port`, the SDK disables gRPC
  proxying for `localhost`, dotted `127.0.0.0/8`, and `::1`. IPv4-mapped loopback and `dns:///` TLS forms retain gRPC
  proxy handling. A plain transport that carries the SDK's keys uses none of these settings (see the plain-transport
  rule below).
- An HTTP endpoint is matched by the host the exporter connects to. `urllib3`, the parser `requests` connects
  with, and the standard library must read the same host from it. A trailing dot, upper case, and valid punycode
  and Unicode spellings match the same host; `ß` and `ss` are different names. A name `requests` refuses, such
  as one with full-width letters, does not match. For a gRPC target, use the ASCII host spelling. The Future AGI hosts
  are `api.futureagi.com`, `grpc.futureagi.com` and the hosts of `FI_BASE_URL`, `FI_TRACES_URL` and
  `FI_GRPC_URL`. `ExporterType.OTLP_HTTP`, `OTLP_GRPC`, `ARIZE`, `PHOENIX` and `LANGFUSE` exporters for one of
  these hosts send only the SDK's headers; to send other headers, use your own collector's host.
- The evals tracer refuses an authority with a backslash, percent sign, white space, control character or user
  information (`@`), an empty authority such as `https:///host`, or a host its two parsers read differently.
  White space around a nonblank endpoint and an `@` after the authority of a plain target are also refused.
  The authority check does not parse gRPC address and socket schemes such as `ipv4:`, `ipv6:` and `unix:` as URLs;
  the gRPC target rule below applies as well. The refusal is a `fi.errors.ConfigurationError` with the code of the
  plain-transport rule below and a constant message that omits the endpoint. Use a plain host name or address with
  no user information. An explicitly supplied experiments collector URL is validated separately during setup; a
  later endpoint refusal inside the exporter factory allows item storage and is reported as a trace export failure.
  An evals endpoint that is empty or only white space counts as omitted, and a blank `FI_BASE_URL` counts as unset
  for the evals trace exporter.
- A gRPC exporter is matched by the host gRPC dials. A Future AGI target is written `host:port`,
  `dns:///host:port`, `http(s)://host:port` or `//host:port`; any other form that names a Future AGI host
  (a `dns://` authority, user information, a target prefix such as `ipv4:` or `unix:`, another scheme)
  raises the same `ConfigurationError`. Targets for other backends, including
  `ipv4:`, `ipv6:` and `unix:` targets, are not refused by this form rule; such a target whose own headers carry the
  SDK's keys over a plain channel has no host the SDK reads, so it raises the `ConfigurationError` of the plain-transport rule
  below without `FI_ALLOW_INSECURE_HTTP=1`, `ipv4:127.0.0.1` included.
  With no explicit endpoint, `ARIZE`, `PHOENIX` and `LANGFUSE` use `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` or
  `OTEL_EXPORTER_OTLP_ENDPOINT` for endpoint validation. The environment-header check can reject credentials
  before that fallback, so specify the endpoint explicitly if those settings carry keys. The experiments exporter
  uses `FI_COLLECTOR_ENDPOINT` or the run's API base URL instead of OpenTelemetry endpoint settings.
- A gRPC exporter bound to `futureagi.com` or a subdomain connects with TLS. An `http://` target or a truthy
  `insecure` argument raises `ConfigurationError` (code `INSECURE_HTTP_REFUSED`). With `insecure=None` and a target
  without `https://`, the exporter also refuses an effective insecure setting of `true` from
  `OTEL_EXPORTER_OTLP_INSECURE` and `OTEL_EXPORTER_OTLP_TRACES_INSECURE`, with the traces setting taking precedence.
  Use `https://host:port` or use `host:port` with `insecure=False`. An `https://` target and the default `False`
  do not consult the insecure settings. A loopback target bound by `FI_BASE_URL`, `FI_TRACES_URL` or `FI_GRPC_URL`
  uses TLS and refuses a truthy `insecure` argument with `insecure_loopback_grpc`. This includes bracketed IPv6
  loopback and IPv4-mapped loopback. A setting with a single `ipv6:` address, such as `ipv6:[::1]:4317`,
  `ipv6:///[::1]:4317` or `ipv6://[::1]:4317`, can bind that address, and a zone id on a loopback setting is ignored
  for binding. A zone id on another address, or an `ipv6:` path with an extra slash after decoding and removing
  the first slash, binds no address. A configured target outside the Future AGI domain and loopback follows the
  plain-transport opt-in below. For a bound TLS connection, the SDK supplies channel credentials instead of
  loading an OpenTelemetry credential provider. It uses `OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE` and, only if that
  setting names a file, `OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY` and `OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE`.
  An unreadable file raises `ConfigurationError` (code `unreadable_tls_file`); correct the path or unset the
  named setting.
- `ConfigurationError.get_error_code()` returns the code itself for `insecure_channel_origin` (a sandbox exec channel
  to a plain-HTTP host outside loopback) and `management_credentials` (credentials that cannot authenticate a gateway
  management call).
- A keyed exporter to a collector outside loopback and the Future AGI domain requires TLS or an explicit opt-in to
  use plain HTTP or gRPC without TLS. Without the opt-in, the check raises `fi.errors.ConfigurationError`
  (code `insecure_http_origin`) before a connection. This is also the code for an ambiguous exporter authority or
  for an omitted endpoint with credentials in `headers=` on `OTLP_HTTP`, `OTLP_GRPC`, `ARIZE`, `PHOENIX` or
  `LANGFUSE`. `FUTUREAGI` instead derives an omitted endpoint from `FI_BASE_URL` or the default API base.
  An experiments run applies the shared HTTP check during trace setup. An invalid explicit `FI_COLLECTOR_ENDPOINT`,
  such as a URL with user information or no host, raises `ExperimentError` earlier. Neither refusal sends a span.
  Put TLS on the collector, or set `FI_ALLOW_INSECURE_HTTP=1` on a trusted network. Only the exact value `1` opts in.
  The shared HTTP check writes one stderr notice naming the host on its first opt-in. The separate OTLP opt-in
  check logs one warning per process; an HTTP exporter whose credentials are detected only by `Authorization`
  or a header value can produce only the stderr notice. A gRPC exporter whose keys are added from `FI_API_KEY`
  and `FI_SECRET_KEY` can log the warning without a stderr notice.
  The opt-in does not permit the SDK's credentials to be sent without TLS to `futureagi.com` or its subdomains.
  It does not affect loopback or HTTPS. Loopback is judged as written: `localhost`, dotted `127.0.0.0/8` and `::1`.
  The gRPC plain-channel check also accepts bracketed IPv4-mapped loopback in `host:port` and `http://host:port`
  targets. A `dns:///` target fails the authority check when `headers=` carries credentials, but can use TLS with
  keys the SDK adds to a bound target. Alternate spellings such as `localhost.`, `127.0.0.1.`, `127.1`,
  `0x7f.0.0.1`, `0177.0.0.1`, `2130706433` and `app.localhost` are not loopback for this rule. For a local collector,
  use `127.0.0.1`. The gRPC check covers `x-api-key`, `x-secret-key`, `authorization`, and header values containing
  a configured SDK key of at least eight characters, as written or encoded. When `FI_API_KEY`, `FI_SECRET_KEY`
  or `FI_PLATFORM_TOKEN` contains such a key, a header value over 64 KiB is also treated as carrying credentials.
  The separate rules below apply to the OpenTelemetry header settings on TLS and plain channels alike.
- A plain transport that carries the SDK's keys ignores the proxy settings. The transports the SDK builds for it
  (the session of an HTTP exporter, a gRPC channel opened with `grpc.enable_http_proxy` set to `0`, the session
  of the evaluation requests of `fi.evals.Evaluator`, and the experiments run exporter) connect to their target
  directly, whatever `HTTP_PROXY`, `http_proxy`, `HTTPS_PROXY`, `https_proxy`, `ALL_PROXY`, `all_proxy`,
  `grpc_proxy`, `NO_PROXY` and `no_proxy` hold, so no key reaches a proxy and `NO_PROXY` entries
  (a CIDR entry, a port, a leading dot) do not decide the opt-in. HTTP exporters use Requests' proxy settings for
  non-loopback HTTPS destinations; HTTPS loopback requests go direct. gRPC uses its own proxy settings. For TLS targets
  written as `host:port` or `https://host:port`, the SDK disables gRPC proxying for `localhost`, dotted `127.0.0.0/8`,
  and `::1`. IPv4-mapped loopback and `dns:///` TLS forms retain gRPC proxy handling.
  A plain send to a loopback address or to another host allowed by
  `FI_ALLOW_INSECURE_HTTP=1` is sent directly and does not go through a proxy from the environment; to send
  through one, put TLS on the collector and use `https://`.
- A keyed `http://` request through a `requests` session passed to `fi.evals.Evaluator` (`session=`) is refused if
  the session would route it through a proxy or uses an adapter the SDK cannot verify. This covers loopback, where
  the session's routing decides. For opted-in non-loopback HTTP, the shared check also considers the environment
  proxy rules. The separate 0.7.1 release included a caller-session rule for `HttpClient`; that release is not in
  this changelog's published history. Breaking: a proxied caller session raises `KeyedProxyRefusedError`
  (a `ConfigurationError`) even for plain loopback. Use an `https://` base URL or let the SDK build the session.
- Version 0.8.1 already refused keyed plain HTTP outside loopback by default for clients such as `fi.datasets`
  and `fi.kb`, with the refusal code named in the exporter entry above and an opt-in for direct sends. Version 0.9.0 includes
  `fi.evals.Evaluator` in the shared HTTP check. For keyed requests, that check refuses malformed authorities such
  as user information or a missing host, and raises `InsecureHttpRefusedError` for plain HTTP to `futureagi.com`
  or a subdomain even with the opt-in. Use HTTPS or a loopback base URL, or use `FI_ALLOW_INSECURE_HTTP=1` for an
  eligible direct send to another host.
- The evals tracer refuses `OTEL_EXPORTER_OTLP_HEADERS` and `OTEL_EXPORTER_OTLP_TRACES_HEADERS` containing
  `x-api-key`, `x-secret-key`, or a value from `FI_API_KEY`, `FI_SECRET_KEY` or `FI_PLATFORM_TOKEN` for endpoints
  outside `futureagi.com` and its subdomains, including configured hosts outside that domain. Within the domain,
  an exporter not bound to a Future AGI host refuses the two key header names, but can send a key held only in
  a value if OpenTelemetry selects that header. The `FUTUREAGI` exporter omits ambient headers. For exporter types
  that can use an OpenTelemetry endpoint fallback, specify the endpoint explicitly if those settings carry keys.
  The refusal identifies the header setting or settings without including any header value. Breaking: the exporter
  raises `ConfigurationError` (code `otel_env_key_headers`); remove the credential-bearing headers from the settings
  or use an explicit HTTPS endpoint bound to a Future AGI host within the domain. `OTLP_HTTP` with credentials in
  its own headers follows the plain-transport rule.
- Experiments collector validation judges loopback on the host as written: `localhost.` and `ⅼocalhost` are not
  loopback. An explicit plain-HTTP collector outside loopback must match the host of a plain-HTTP API base and pass
  the exporter checks. Collector validation refuses a host made only of digits and dots that is not a valid address,
  such as `127.1`, for both HTTP and HTTPS.
- Read `error.code` or `get_error_code()` to identify a refusal regardless of message wording. The exporter-specific
  endpoint form, gRPC TLS and TLS file messages end with the code in parentheses. The shared HTTP check, including
  when it refuses a gRPC target, the empty-endpoint check and the environment-header check outside the Future AGI
  domain omit the code from their messages. Within the domain, the refusal for a key header name on an unbound
  exporter includes the code in parentheses.
- `FI_COLLECTOR_ENDPOINT` of `""` counts as unset, so the run sends to `/tracer/v1/traces` under its base URL, while a
  value of only white space is refused.
  A blank `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` counts as unset for `ARIZE`, `PHOENIX` and `LANGFUSE`
  exporters, as the other blank settings do.

### Changed: configuring evaluations without OpenTelemetry
- `Evaluator.evaluate(..., platform=..., custom_eval_name=...)` uses OpenTelemetry to read the current span.
  If the import fails, it raises `fi.errors.MissingExtraError` before sending a request and suggests
  `pip install "futureagi[evals]"`. For Langfuse, supplying only one key raises `fi.errors.AuthError`
  before the OpenTelemetry check.

### Changed: refused and timed-out evaluations
- When the eval endpoint refuses an evaluation, `Evaluator.evaluate()` returns a result with a reason.
  The reason uses the server's message or field errors, followed by the HTTP status (for example,
  `Validation failed: inputs: ... (HTTP 400)`). If neither is available, it gives the status and a short
  excerpt or says the body is empty. A 403 adds `Check your API key and secret key.`
- A request that timed out has the reason `Evaluation timed out after <n>s`, also when the
  HTTP request itself timed out. `evaluate(..., engine="turing")` reports a refused, failed or
  timed-out request as status `failed` with that text as `error` instead of a completed result
  with no score.

### Changed: dependency floors
- Raise the base dependency minimums to anyio 4.14.2, certifi 2026.10.18,
  idna 3.15, requests 2.33.0 and urllib3 2.8.0 to exclude versions affected
  by published advisories. Retain the anyio <5 upper bound.

### Changed: dataset error compatibility
- SDK-owned `fi.utils.errors.RateLimitError` / `ServerError` also subclass their
  `fi.errors` counterparts, retaining `DatasetError` catches, legacy messages and
  `(message=None, cause=None)` constructors. No `fi.RateLimitError` / `fi.ServerError`
  root aliases are added; the dataset 503 `ServiceUnavailableError` stays as it is.
- Legacy construction has no response metadata: inherited status fields are nominal
  429 / 500 with `payload=None`, not the observed 5xx response. Copy and pickle retain
  the legacy one-message reconstruction; exception causes are not serialized.
- This bridge requires futureagi's own `fi/utils/errors.py`. If an older sibling
  distribution overwrites it, its dataset hierarchy wins; `fi.errors` stays SDK-owned.

### Security: evaluation-template cache
- The evaluation-template cache in `fi.evals` keys successful fetches by a normalized base URL and a digest of
  both the API and secret keys. Entries expire after 300 seconds, and a failed fetch clears the relevant cache.
  This applies when migrating from the separate `ai-evaluation` package to futureagi 0.9.0; futureagi 0.6.13
  and 0.8.1 did not include `fi.evals`.

### Deprecated: string audio paths
- Bare string audio uploads send literal content by default, as in 0.8.1. The new
  `audio_upload_mode="normalized"` option on `AgentCC` and `AsyncAgentCC` treats bare strings as file paths.
  Its `DeprecationWarning` recommends `pathlib.Path(...)` and announces `TypeError` for bare strings in 1.0.
- In normalized mode, string paths containing NUL, newline or carriage-return characters raise `TypeError` before any file
  read. Paths are opened read-only, and no request is sent if opening fails. Bytes, binary files and tuples with bytes
  content are sent as given; an `os.PathLike` path is read and sent under its file name, and a tuple whose content is an
  `os.PathLike` path is read and sent under the tuple's own file name.

### Changed: optional evaluation dependencies
- Local metrics and LLM judges require Python 3.11+ and `futureagi[evals]`. The base SDK requires Python 3.10+;
  the cloud evaluation client ships in the base installation and does not require `[evals]` for ordinary
  cloud evaluations. Other extras follow their own Python version markers.
- `[evals]` installs LiteLLM on Python 3.11-3.14 (`>=3.11,<3.15`). Use that range for LiteLLM-backed
  judges, providers, grading criteria and feedback-store embeddings. If the code reaches the LiteLLM import
  and LiteLLM is absent, it raises `ModuleNotFoundError` for `litellm`; on Python 3.15+ the message gives
  the supported range. On Python 3.10, local evaluation imports report the Python 3.11 minimum first.
- `[evals]` requires LiteLLM 1.100.4 or later below 2.0, excluding 1.101.0, 1.101.1, 1.101.2,
  1.102.0, 1.102.1 and 1.103.0 under a published advisory. Its OpenAI range (`>=1.109.1,<3`) permits
  OpenAI 2.x. The separate `[openai]` extra installs the OpenAI instrumentor and tracing dependencies.
- `[evals]` requires filelock 4.2.1+ and includes rouge-score, which 0.8.1 installed with the base SDK.
  An installer using the rouge-score source distribution builds it from source; base installs do not
  require that build. The cloud client imports without rouge-score. If a local ROUGE metric is used
  without it, the error names `futureagi[evals]` and Python 3.11+.

### Changed: agent-learning-kit namespace
- The separate `agent-learning-kit` distribution owns `fi.alk` and its subpackages. Like 0.8.1,
  futureagi ships no `fi/alk/` files. Version 0.9.0 includes the SDK's `fi.evals` package;
  0.8.1 excluded it.
- If no installed package provides `fi.simulate` or `fi.opt`, the SDK gives an import error pointing to
  `fi.alk.simulate` or `fi.alk.optimize`. Moved evaluation names and the report module name their
  `fi.alk.evals` replacements. The SDK does not import or install ALK, and namespace extension supports
  separate install paths.

### Changed: credential isolation
- `APIKeyAuth` already stored credentials on each client instance in 0.8.1. In 0.9.0, reading
  `_fi_api_key` or `_fi_secret_key` from the class or an SDK subclass returns `None` and also emits
  a `DeprecationWarning` that contains neither key. Read those attributes from the client instance.
- `APIKeyManager` shares credentials process-wide and is unsuitable as a per-tenant store;
  credential isolation applies only to `APIKeyAuth` client instances. This release
  emits no deprecation warning for the manager.

### Added: late-span tag on experiment traces
- With `trace=True`, `upload=True` and a finite `timeout_s`, the SDK exporter sets the boolean attribute
  `fi.trial.after_deadline=true` on exported non-root trial spans, including evaluator spans, that end at or after
  the trial deadline. Retries share that deadline. The exporter removes any caller-supplied value for this
  attribute from the exported copy, including on root and on-time spans and spans from trials without a timeout.
  The SDK does not add the tag to open spans or to spans sent by a caller's tracing provider.

### Experiment trace export
- Uploaded experiments using `trace=True` raise `TraceExportError`
  (`TRACE_EXPORT_FAILED`, CLI exit 3) and emit one `TraceExportWarning` per run when
  an OTLP batch fails (including collector HTTP 404/405/5xx or connection failures),
  even with `progress=False`. Warning promotion keeps the typed error or an existing
  primary failure, including interruption. Diagnostics name the endpoint's scheme, host and port (not its
  path) and the status, not response bodies or secrets. Nonconnection request errors do not trigger retries. The error
  suggests `trace=False` (CLI `--no-trace`) for future runs without tracing. Items may already
  be stored; spans are not journaled and resume cannot recover them. Batch-processor queue
  drops, HTTP 200 OTLP partial rejections and caller-owned exporters are outside this terminal-batch check.
  With credentials and without `--offline`, `futureagi-py doctor` sends a GET to `/tracer/v1/traces` at the API
  base URL, not to a custom `FI_COLLECTOR_ENDPOINT`. HTTP 404 is a setup problem; a transport exception is
  inconclusive ("could not check") and does not affect the exit code. The GET does not verify POST export.

### Unsupported legacy helpers
- **Unsupported legacy helpers report the server limitation explicitly.**
  `EvalTemplateManager.get_ground_truth_config`, `set_ground_truth_config` and
  `search_ground_truth` retain their signatures and raise
  `fi.errors.PlatformNotConfiguredError` (`code="unsupported_operation"`) before HTTP.
  The SDK has no compatible replacements for the config and search routes, which the platform removed before 1.56.1.
  `fi.client.Client.log` retains its signature, validation and
  `POST /sdk/api/v1/log/model/` request and emits a `DeprecationWarning`; an HTTP 404
  raises `fi.client.LegacyModelLogUnavailableError`, a `requests.HTTPError`.
  `list_ground_truth(template_id)` reads
  dataset state, not the old template config (`mode` and `injection_format` are
  unavailable). Atomic setup requires both mappings and cannot set `mode`,
  `similarity_threshold` or `injection_format`. `get_ground_truth_data` reads
  paginated rows, not similarity-search results. For tracing, use traceAI
  instrumentation to emit traces and `client.tracing` on a `FutureAGIClient` to
  query them; neither accepts the old model-log payload as a drop-in replacement.
  `Client.log` was present in futureagi 0.6.13; that wheel did not contain
  `fi.evals` or these ground-truth helpers.

### Changed: experiments
- Discard task results that arrive at or after the trial timeout, including cancellation-suppressing async tasks and late sync tasks, without evaluating or journaling them as completed.

### Licensed operations and HTTP 402
- On `FutureAGIClient`, HTTP 402 raises `PaymentRequiredError`; `402 LICENSE_MISSING` raises its
  `LicenseRequiredError` subclass. Both can be caught as `FutureAGIAPIError`. The missing-licence message asks
  the server administrator to configure an Enterprise licence. Other 402 responses expose the server code
  and parsed payload when available.
- Missing-licence messages name the server-reported feature when available. Tracing
  examples explain the licence requirement before calling error-feed operations;
  `help(fi.errors)` includes the error tree and legacy namespace caveat.
- The Python error-feed methods (`tracing.issues`, `issue`, `issue_stats`) and generated feed operations document
  the Enterprise licence requirement for servers you operate and the eligible-plan requirement in the cloud.
  Dataset user-eval methods document the conditional Turing/Protect model gate (`ENTITLEMENT_DENIED`, not
  `LICENSE_MISSING`), which does not apply to code evaluations. The SDK also supports legacy error imports.
- The same model-gate documentation applies to legacy `Dataset.add_evaluation` from futureagi and
  `EvalTemplateManager.run_playground` from the separate `ai-evaluation` package. On a model-gate denial,
  those methods continue to raise `DatasetError` and `Exception`, respectively.

### Console API availability errors
- A complete Console 404 without a Console/EE API error envelope raises `fi.errors.ConsoleUnavailableError`,
  a `NotFoundError` subclass also exported by `fi`, in both sync and async clients. The diagnostic uses the
  failing response without a preflight, and shows the host and any explicit port, not the path. Responses with
  a recognized error envelope retain their status and code classification, including `ProductNotAvailableError`.
  Console access through this SDK is unavailable on Future AGI Cloud in this release. For an Enterprise deployment
  you operate, set `FI_PLATFORM_BASE_URL` to the Console API origin or check the configured URL. If the origin
  comes from a saved login, the diagnostic points to that login.
- Capped or interrupted 404 bodies do not prove Console unavailability; when the EE
  envelope cannot be parsed, retain status-only `NotFoundError` classification. This
  also applies to oversized HTML error pages, even with a `text/html` content type.

### Changed: published compatibility
- Bulk annotation and queue response models keep the snake_case names published in 0.7.0 and retained in 0.8.1.
  Version 0.9.0 accepts legacy camelCase input aliases for bulk annotations and 32 queue fields, and adds
  camelCase read/write properties for bulk annotations. Each alias warns once per process. Schemas and
  dictionary and JSON dumps, including nested models and `by_alias=True`, use the published snake_case names.
  Extra-field and exclusion handling follows Pydantic; the aliases apply to response models, not request payloads.
- `EmbeddingResponse` keeps accepting `Usage` instances and defaulting missing completion tokens to zero,
  as in 0.8.1. Version 0.9.0 adds the `EmbeddingUsage` subtype for dictionary inputs and accepts its instances
  without changing the public `Usage` field annotation.

### Changed: dataset payloads
- `Dataset.add_run_prompt` sends `max_tokens`, `temperature`, `presence_penalty`,
  `frequency_penalty` and `top_p` under `config.run_prompt_config`, matching the
  server's readers. Model, messages, output format, concurrency, tools, tool
  choice and response format are direct children of `config`. Explicit zero
  values and supplied empty tools/response formats are retained; omitted
  optional fields stay absent. Public argument names, order, types, defaults,
  validation, column translation and return identity stay the same. The payload
  change is in the 0.9.0 client, not the server or the published 0.6.13 package.

### Changed: published compatibility
- `BulkAnnotationResponse` accepts the 0.6.13 spellings `annotationsCreated`, `annotationsUpdated`,
  `notesCreated`, `succeededCount`, `errorsCount` and `warningsCount` as constructor inputs and read/write
  attributes. Model fields and serialized names use the snake_case spellings from 0.7.0 and 0.8.1.
  Extra fields are ignored.
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
- Restore `fi.api.auth.DatasetNotFoundError` for 0.6.13 compatibility. As in 0.8.1, `fi.client` exports
  `HttpMethod`, `RequestConfig` and `Routes`, and `AnnotationQueue.list_queues` accepts `page_size=20`.
  Queue and item listing send `page_size` as `limit` and keep the 1-based `page` and the existing defaults.
- Queue `create` displays `OMITTED_LABEL_IDS` in its Python signature instead of an
  object address.

### Changed
- List methods on `FutureAGIClient` document accepted pagination parameters and
  page-number bases. Generated tracing and integration operations do not declare
  unsupported dialects; callers can use size aliases supported by the server. Free-form
  paging kwargs reach the server as given, with no page-base translation.
  Alert details also accept zero-based pagination for their nested log list.
- The generated template-labels operation accepts `template_id` and `template_name` and does not declare
  pagination parameters.
- `FutureAGIClient` returns server success envelopes for enveloped alert operations, queue archive, dataset row
  and column deletion, evaluation template and dataset evaluation deletion, and experiment deletion.
  Annotation labels (both aliases), alert logs, annotation queues and items, experiments, scores, prompts,
  prompt labels and prompt versions retain pagination fields such as `total_pages` and `current_page`
  when the server supplies them. Prompt-version listing accepts a 1-based `page` and a `limit`.
  Bare DRF responses stay bare; no-content deletes return `None`.
- Queue `create` accepts omitted `label_ids`, with one `DeprecationWarning` saying
  that callers must supply them in a future version. `get_or_create_default` uses exactly one legacy scope
  to obtain labels; that lookup can create or restore the default queue even if the
  label check then fails, but the SDK does not scope the new queue. If no single scope or
  no usable labels exist, `fi.queues.DefaultQueueLabelError` (a `ValueError`, also
  exported from `fi`) explains why no truthful default is available. Explicit label
  ids avoid this lookup and warning. The legacy project, dataset and agent-definition
  fields have equal priority for default-label lookup; none scopes the new queue.
- The Python SDK adds the `futureagi-py` console script and registers its command groups under `futureagi.cli`.
  `python -m fi._cli` runs the same CLI. Install with `pip install futureagi` and import `fi`.
  The `futureagi` executable is the standalone Future AGI CLI.
- **Ground-truth mapping setters in `fi.evals` use atomic `PUT /model-hub/ground-truth/{id}/setup/`.**
  When migrating from `ai-evaluation` 1.1.0, pass the other mapping, `max_examples` (an integer from 1 to 20)
  and `enabled` (a boolean) as keywords. Read current values with `list_ground_truth(template_id)`;
  setup replaces the complete configuration. Missing values, invalid `max_examples` or `enabled`, and
  unrecognized role keys raise `fi.errors.ConfigurationValueError`, a subclass of `ConfigurationError`
  and `ValueError`. Accepted roles are `output` and `explanation`, with aliases `expected_output`,
  `reasoning` and `reason`. The `input` and `score` roles documented by `ai-evaluation` 1.1.0 are rejected.
  The SDK documents that the platform activates this dataset and deactivates the other datasets for the same
  template, organization and workspace, even with `enabled=False`. After changing `variable_mapping` on a
  COMPLETED dataset, the documented transition is to PENDING; call `trigger_ground_truth_embeddings(ground_truth_id)`
  to regenerate embeddings.
  The ground-truth config and search methods raise `PlatformNotConfiguredError` before HTTP; their legacy
  route constants are exported for source compatibility. `Client.log` validates and sends its
  legacy request, emits a `DeprecationWarning`, and raises `LegacyModelLogUnavailableError` on HTTP 404.
  For tracing, use traceAI instrumentation to emit traces and `FutureAGIClient.tracing` to query them;
  neither is a drop-in replacement for the model-log payload.
- Require Python >=3.10; supported classifiers are 3.10 through 3.13.
- Raise the `anyio` minimum from 4.0 to 4.14.2; retain the `fi/py.typed` marker shipped in 0.8.1.
- Bundle webhook verification and management in `fi.webhooks` in the `futureagi` distribution.
  The standalone webhook source project is not a separate release artifact.
- The 0.8.1 wheel already includes the `fi.gateway` data-plane client (`AgentCC` and `AsyncAgentCC`).
  The 0.9.0 wheel and source distribution include it and omit tests and bytecode. Raise the
  `typing-extensions` minimum from 4.7 to 4.12.2. Packaging checks do not establish live gateway behavior.
- Platform namespaces are 0.x APIs.

### Deprecated
- The SDK accepts the restored camelCase inputs and exposes the bulk response attributes.
  Prefer the corresponding snake_case field (for example `annotations_created`
  or `created_at`). Using each old alias warns once per process with a
  `DeprecationWarning` naming the new field; canonical-only construction and
  access are silent. When both inputs are present, the canonical value wins.

### Added
- Gateway HTTP-backed chat and text completion streams support `with` and `async with`. Exiting closes
  the response and discards unread chunks, including on early exit or a body exception. A cleanup error
  can take precedence over the body exception. `close()` and `aclose()` are idempotent, as in 0.8.1.
  Closed streams and their existing iterators are exhausted, including buffered SSE and cache-hit JSON;
  re-entering a closed stream does not reopen it. Closing during a pending read attempts to release the
  response without raising a generator-busy error from iterator cleanup. The pending reader may report
  a transport interruption; wait for that reader to finish before iterating again.

### Not in this release

- The Python `fi.simulate` facade is not offered; its import error points to `fi.alk.simulate`.
  The sync and async `fi.platform` clients retain the `simulation` resource shipped in 0.8.1.

## [0.8.1](https://github.com/future-agi/futureagi-sdk/compare/python-v0.8.0...python-v0.8.1) (2026-11-28)


### Bug Fixes

* **python:** send API keys only to the configured host over https or loopback ([5491aab](https://github.com/future-agi/futureagi-sdk/commit/5491aaba0dd0940193840d0e1d64004c32f43848))

## 0.8.1

### Changed

* A request that carries an API key to an `http://` host that is not loopback is refused before a connection is made, with `ValueError` (`AgentCCError` for `fi.gateway`) and the code `insecure_http_origin`. `fi.kb` raises the `ValueError`. `fi.datasets` raises `DatasetError` from `get_dataset_config`, from the calls built on it and from `Dataset(dataset_config=...)`, with the same code as `.code` and from `get_error_code()`, and the refusal as its context; the `Dataset` instance methods that send raise the `ValueError`. `Prompt(template=...)` that looks a template up by name logs a refused lookup as a template it did not find and keeps the template it was given. A request carries a key when its headers hold `X-Api-Key`, `X-Secret-Key`, an `Authorization` header with a Bearer or Basic value, or a cookie named `X-Api-Key` or `X-Secret-Key`. The entries below say which request is checked.
* Set `FI_ALLOW_INSECURE_HTTP=1` or pass `allow_insecure_http=True` to the client to send such a request; it then goes directly to the host, and not through `HTTP_PROXY`, `ALL_PROXY`, a session `proxies` setting or an `httpx` proxy. `FI_ALLOW_INSECURE_HTTP` is read at each request, not when the client is created. `health_check`, `check_valid_key` and `ProviderAPIKeyClient` read the opt-in from `FI_ALLOW_INSECURE_HTTP` only; `health_check` and `check_valid_key` raise the refusal (`AgentCCError`) rather than reporting a failed check.
* The `fi.prompt` classmethods that build their own client accept `allow_insecure_http`: `Prompt.list_templates`, `Prompt.delete_template_by_name`, `Prompt.get_template_by_name`, `Prompt.assign_label_to_template_version`, `Prompt.remove_label_from_template_version`, `Prompt.set_default_version` and `Prompt.get_template_labels`.
* The opt-in does not unlock a host written with userinfo (`user@host`), non-ASCII characters in the host or port (including ideographic or fullwidth full stops such as `127。0。0。1`, fullwidth digits, and characters that lower-case to ASCII, such as U+212A KELVIN SIGN; a host in IDNA form, `xn--…`, is ASCII and follows the rules above), `%`, a trailing dot (`localhost.`), or an IPv4 address in a short, whole-number, hex, octal or zero-padded form (`127.1`, `2130706433`, `0x7f.0.0.1`, `0177.0.0.1`, `127.000.000.001`).
* `http://` to a loopback host (`localhost`, `127.0.0.0/8`, `::1`) is sent directly. `0.0.0.0`, `::ffff:127.0.0.1`, `localhost.localdomain`, names under `.localhost` (such as `foo.localhost`) and `host.docker.internal` are not loopback for this rule, so a keyed plain-`http://` request to them needs the opt-in. The `httpx` clients the SDK builds for `fi.platform` and `fi.gateway` send plain `http://` through no proxy.
* For the clients built on `fi.api` (`requests` sessions; among them `fi.datasets`, `fi.prompt`, `fi.kb`, `fi.annotations` and `fi.queues`), the key check runs on the request as the session prepares it, with the session's headers, cookies and authentication (or `.netrc` credentials) applied. It runs again on each request that a response hook sends through the response's connection (`response.connection.send`), as challenge authentication such as `requests.auth.HTTPDigestAuth` does: such a request with a key is refused when its host may not receive the key over plain `http://`, or when it would go over plain `http://` through a proxy (the `proxies` given to that send) or through an adapter that is not exactly `requests.adapters.HTTPAdapter`. The same check runs on a request that a response hook of the SDK's request sends through `send` of the session given to the client, or of a session it wraps as `.session` (`session.send`), while the hook runs, on the thread that runs it; the proxies are those given to that send, else the session's `proxies` and, under `trust_env`, the environment's.
* Without the opt-in, these clients refuse a plain-`http://` request to a host that is not loopback even when it carries no key, if the session or the request has a response hook (including one its authentication registers) or the adapter mounted for its URL is not exactly `requests.adapters.HTTPAdapter`. To a loopback host, or with the opt-in, such a request is sent through no proxy. A keyed plain-`http://` request whose adapter is not exactly `requests.adapters.HTTPAdapter` (a subclass included) is refused, to a loopback host and with the opt-in as well. Each redirect hop is judged the same way: a hop to plain `http://` on a host that is not loopback, without the opt-in, is refused before it connects when the session has authentication or a response hook, when the request has a response hook, or when the adapter for the hop's URL is not exactly `requests.adapters.HTTPAdapter`; a hop that is sent is refused when the proxies `requests` uses for it (the session's `proxies`, and the environment proxies under `trust_env`) would carry it.
* Requests that your own code sends through `session.send` are not checked, apart from one that a response hook of the SDK's request sends while it runs, on its thread; such a send is judged with the plain http opt-in of the client whose request ran the hook. Requests that your own response hooks send in other ways are not checked: through `requests.Session.send` called on the class, a `send` read from the session before it was given to the client, a `send` set on the session object after it was given to the client, a session or adapter that the client does not hold, the `send` of an adapter the session holds called directly (such as `session.get_adapter(url).send`), or another thread (for example `FuturesSession.request` from a hook). These checks also do not cover a `requests.adapters.HTTPAdapter` whose `send` is replaced on the instance; an adapter or session that chooses its own proxy (an `HTTPAdapter` whose `poolmanager` is a `ProxyManager`, or a session subclass that overrides `request` or `rebuild_proxies`); a session subclass that replaces the prepared request's hooks instead of adding to them (its redirects are then not checked either); a key that a custom adapter adds inside its own `send` (the SDK gives such an adapter `proxies` that send plain `http://` directly, and an adapter that does not use them is outside the check); or a session object that is neither a `requests.Session` nor a wrapper holding one as `.session`, for which only the headers the SDK passes are checked.
* For `fi.platform` and `fi.gateway`, the request checked is the one the `httpx` client builds (`build_request`): its URL resolved against the client's `base_url`, with the client's `params`, default headers and cookies. The URL as written is checked as well. A URL, header or transport that the `httpx` client's own `auth`, its request event hooks, an overridden `send`, or a custom transport whose `handle_request` changes the URL change after the request is built is not checked.
* An `httpx` client passed as `http_client` may carry a keyed plain-`http://` request when the transport it selects for that URL (from its `proxy=`, its `mounts`, and the environment proxies it read under `trust_env` when it was built), including transports that a custom transport holds in its attributes or in the dicts, lists, tuples and sets they hold, goes through no proxy (a transport reached only through a function, bound method, closure or `functools.partial`, held in any other object (such as a plain object, a dataclass, a `types.SimpleNamespace`, a `collections.deque` or a `types.MappingProxyType`) or as a dict key, or an `httpcore` pool held under an attribute other than `_pool`, is not seen). A transport that holds a connection pool counts as going through no proxy only when that pool is exactly `httpcore.ConnectionPool` or `httpcore.AsyncConnectionPool` (not a subclass), built without `proxy=`, with no `handle_request`, `handle_async_request` or `create_connection` set on the pool object, and with httpcore's own network backend (`SyncBackend` for the sync pool; `AutoBackend`, the default, `AnyIOBackend` or `TrioBackend` for the async pool) with no `connect_tcp` or `connect_unix_socket` set on the backend object; an `AutoBackend` that holds the backend it hands connections to counts only when that backend is exactly `AnyIOBackend` or `TrioBackend`, under the same rule. Any other pool or backend (a pool subclass, a pool built with `proxy=`, another network backend, or one with such a method set on the object) is treated as one that may use a proxy. Connections that your own code places in a pool are not checked. A client whose transport lookup is missing, raises or returns something that is not an `httpx` transport, or whose `httpx` HTTP transport for the URL holds no connection pool, is treated as one that may use a proxy; otherwise the request is refused with the same error and code. A caller's client whose transport for the URL is `httpx.MockTransport`, `WSGITransport` or `ASGITransport`, or a subclass of one, is treated as making no connection and is not checked, for any host; requests that its handler, its application or the subclass makes itself are outside the check.
* Redirects of keyed requests sent with `requests` (the `fi.api`-based clients such as `fi.kb`) are followed when the target may carry the key: the target is the URL `requests` connects to, a plain-`http://` target follows the rules above and is sent directly, through no proxy (with the opt-in, such a target may be on another host; `fi.platform` follows redirects to the same origin only), and a `Location` holding a control character, DEL or whitespace is refused. A refused redirect raises `ValueError` with the code `insecure_http_origin` and is not retried.
* Session authentication (or `.netrc` credentials) runs once per attempt, and the request it produced is the one checked and sent. An error it raises ends the attempt without a send; it is retried like a failed send and, on the last attempt, raised to the caller. A redirect that would add a key, through a cookie named `X-Api-Key` or `X-Secret-Key` or through `.netrc` credentials, is checked as a keyed request.
* `fi.datasets` serves a cached dataset config, and `fi.prompt` a cached prompt template, only to a call with the same base URL, the same API and secret keys, and the same plain http opt-in (`allow_insecure_http`, else `FI_ALLOW_INSECURE_HTTP`). A dataset config entry holds the config only: each call gets a `Dataset` built from its own arguments and environment (keys, base URL, opt-in and session).
* `fi.gateway` clients do not follow redirects; a `3xx` response raises `APIStatusError` with its status code.
* `https://` requests get only the redirect and connection checks above. A plain-`http://` request without a key gets only the response hook and custom adapter rule above and this one: from the `fi.api`-based clients, a plain-`http://` request to a loopback host, or with the opt-in, goes through no proxy when its session may add a key (session authentication, a key header or cookie, a response hook, a custom adapter, or `trust_env`, which `requests` turns on by default).
* These rules apply to the `fi` package in this distribution (`futureagi`). `fi.evals` and `fi.integrations.otel` are not part of it (the build excludes them), so the rules do not cover them.
* Each client other than `APIKeyManager` sends its own keys, including for knowledge-base uploads and when several clients are created at once. `APIKeyManager` (`fi.api.auth`) is one object per process, shared by every caller. Each time it is created (`APIKeyManager()`) it reads `FI_API_KEY` and `FI_SECRET_KEY` from the environment, so every holder sends the keys of the latest creation; a creation that finds either variable unset raises `MissingAuthError` and sets both keys of the shared object to `None`. Its `headers` raise `MissingAuthError` when it has no keys, and its `request` then sends without key headers. Its provider keys (`get_api_key`, `set_api_key`) are read from the environment when it is first created and are shared by every holder: a key set through `set_api_key` applies to every holder, and a later `APIKeyManager()` does not read them again.
* A client given only one of its two keys (an API key or a secret key), or an empty value for one, takes the missing key from `FI_API_KEY` or `FI_SECRET_KEY`, one key at a time. Pass both keys so that a client reads neither variable.
* Code in the same process that replaces or patches `httpcore` or `httpx` classes, functions or object internals (such as a method or attribute set on a live connection pool or network backend object) is not checked.

## [0.8.0](https://github.com/future-agi/futureagi-sdk/compare/python-v0.7.0...python-v0.8.0) (2026-11-21)


### Features

* **sdkgen:** generate the platform SDK reference for docs.futureagi.com ([#42](https://github.com/future-agi/futureagi-sdk/issues/42)) ([d9625dc](https://github.com/future-agi/futureagi-sdk/commit/d9625dc2e150f82208b1cc586587f87477ce5f63))


### Bug Fixes

* handle UnboundLocalError in Prompt._handle_error on 400 responses ([5b8a98f](https://github.com/future-agi/futureagi-sdk/commit/5b8a98f8275812aa0e83afbf0929bf4dca126566))

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
