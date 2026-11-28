"""Future AGI keys in ``OTEL_EXPORTER_OTLP_HEADERS`` and ``OTEL_EXPORTER_OTLP_TRACES_HEADERS``.

The OpenTelemetry exporters read those variables themselves and send them to the exporter's endpoint, so the check runs
on the endpoint the exporter will use. A key is carried when a header is named ``x-api-key`` or ``x-secret-key``, or when
any header value holds one of the SDK's keys as text (as written, percent-decoded once or twice), whatever the header is
named. An exporter that does not send to Future AGI refuses a carried key; an exporter that does follows the plain-http
rule of the exporter's own headers.
"""

from __future__ import annotations

import os
from typing import Mapping, Optional
from urllib.parse import unquote, urlsplit

from fi._core.proxy_routing import normalize_header_name
from fi.errors import ConfigurationError

_OTEL_HEADER_VARIABLES = ("OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS")
_KEY_HEADER_NAMES = frozenset({"x-api-key", "x-secret-key"})
_FI_KEY_VARIABLES = ("FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN")


def _carries_key(value: str, keys: set[str]) -> bool:
    """Whether the header list ``value`` names a key header or holds a key as text."""
    texts = {value, unquote(value), unquote(unquote(value))}
    if any(key in text for key in keys for text in texts):
        return True
    names = {normalize_header_name(unquote(pair.split("=", 1)[0])) for pair in value.split(",") if "=" in pair}
    return bool(names & _KEY_HEADER_NAMES)


def require_no_key_headers_in_otel_env(
    endpoint: str,
    environ: Optional[Mapping[str, str]] = None,
    *,
    plaintext: bool = False,
) -> None:
    """Raise ``ConfigurationError`` (code ``otel_env_key_headers``) when an OTLP header variable carries a Future AGI key
    and ``endpoint`` is not a Future AGI address; for a Future AGI address the key follows the plain-http rule
    (``insecure_http_origin`` over ``http://``, which no opt-in allows for a Future AGI host). ``plaintext`` says a
    scheme-less endpoint is a plain channel (a gRPC target). The error names the variable and no header value."""
    from fi._core.http_security import require_secure_credentials_url
    from fi._core.origins import in_future_agi_zone

    env = os.environ if environ is None else environ
    keys = {env.get(name, "") for name in _FI_KEY_VARIABLES} - {""}
    carrying = [variable for variable in _OTEL_HEADER_VARIABLES if _carries_key(env.get(variable) or "", keys)]
    if not carrying:
        return
    text = endpoint if "://" in endpoint else "//" + endpoint
    try:
        host = (urlsplit(text).hostname or "").lower().rstrip(".")
    except ValueError:
        host = ""
    if host and in_future_agi_zone(host):
        url = endpoint if "://" in endpoint else ("http://" if plaintext else "https://") + endpoint
        require_secure_credentials_url(url, setting="the exporter endpoint", proxies_disabled=True)
        return
    variable = carrying[0]
    raise ConfigurationError(
        f"{variable} names a Future AGI key header (or a header that holds a Future AGI key) and this exporter does not send to Future AGI. "
        f"Remove that header from {variable}, or point the exporter at a Future AGI address.",
        code="otel_env_key_headers",
    )
