"""FA management semantics over the shared policy executor; no service URLs."""
from __future__ import annotations

import warnings
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from fi._core.errors import api_error
from fi._core.origins import PlatformOrigin, parse_origin
from fi._core.pagination import AsyncPage, Page
from fi._core.policy import PaginationSpec
from fi._core.raw import CallMeta, Namespace
from fi._core.redact import redact_value, scrub_value
from fi.errors import ConfigurationError, FutureAGIAPIError


class GatewayConfigWarning(UserWarning):
    """A configuration was stored with warnings or has not reached the gateway."""


class GatewayConfigWarningError(ConfigurationError):
    """Strict-mode warning; the server mutation may already have applied."""


def management_origin(credentials: Any) -> PlatformOrigin:
    """Use the resolved FA origin and personal key pair, never an EE or gateway token."""
    if credentials.platform_token:
        raise ConfigurationError("Gateway management requires a personal platform key pair", code="management_credentials")
    credentials.require()
    if any(str(v).startswith("sk-agentcc") for v in (credentials.api_key, credentials.secret_key)):
        raise ConfigurationError("A gateway key cannot authenticate management calls", code="management_credentials")
    headers = {"X-Api-Key": credentials.api_key, "X-Secret-Key": credentials.secret_key}
    for name, value in (("X-Workspace-Id", credentials.workspace_id), ("X-Organization-Id", credentials.organization_id)):
        if value:
            headers[name] = value
    url = parse_origin(credentials.base_url)
    return PlatformOrigin(url=url, mode="keys", source="derived",
                          headers=headers, secrets=(credentials.api_key, credentials.secret_key), custom=False)


def validate_body(name: str, body: Any) -> None:
    """Refuse key ownership changes and unenforced limits before any request."""
    if name == "gateway.keys.update" and isinstance(body, Mapping):
        forbidden = {"user", "owner", "organization", "workspace", "type", "rate_limit_rpm", "rate_limit_tpm", "allowed_ips"}
        if forbidden.intersection(body) or (isinstance(body.get("metadata"), Mapping) and
                {"rate_limit_rpm", "rate_limit_tpm", "allowed_ips"}.intersection(body["metadata"])):
            raise ConfigurationError("Key ownership and unsupported limits cannot be changed", code="unsupported_key_field", operation=name)


def mask_read(value: Any) -> Any:
    """Conservatively mask credential dictionaries, including short and nested values."""
    if isinstance(value, list):
        return [mask_read(v) for v in value]
    if not isinstance(value, Mapping):
        return value
    return {k: (_mask(v) if k in {"credentials", "encrypted_credentials", "api_key", "secret_key", "key", "token"}
                else mask_read(v)) for k, v in value.items()}


def require_personal_keys(value: Any) -> None:
    """Refuse legacy organization-owned records rather than presenting them as personal keys."""
    if isinstance(value, list):
        for row in value:
            require_personal_keys(row)
    elif isinstance(value, Mapping):
        if "results" in value:
            require_personal_keys(value["results"])
        elif "id" in value and (not value.get("user") or value.get("type") in {"system", "mcp"}):
            raise ConfigurationError("The backend returned a non-personal gateway key", code="non_personal_gateway_key")


def _mask(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _mask(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_mask(v) for v in value]
    return None if value is None else "[REDACTED]"


def scrub_management_value(value: Any, secrets: Any) -> Any:
    """Scrub decoded string values once, including short secrets, without changing wire keys."""
    return scrub_value(value, secrets, min_length=1, scrub_keys=False)


def unwrap(value: Any, name: str, secrets: Any, *, meta: CallMeta, strict: bool = False) -> Any:
    """Unwrap FA envelopes; do not turn a false-status body into a successful result."""
    if isinstance(value, Mapping) and "status" in value:
        if value["status"] is False or value["status"] in ("error", "failed"):
            safe = scrub_management_value(value, secrets)
            raise api_error(400, redact_value(safe), meta.headers, operation=name,
                            idempotency_key=meta.idempotency_key, body=safe)
        if "result" not in value:
            raise FutureAGIAPIError(200, None, code="invalid_envelope", operation=name)
        value = value["result"]
    if name.startswith("gateway.keys."):
        require_personal_keys(value)
    # Interpret server semantics before redaction; credentials can collide with wire field names.
    if isinstance(value, Mapping) and (value.get("gateway_synced") is False or value.get("warnings") or value.get("gateway_warning")):
        # Do not echo arbitrary server warning text: it can contain reflected credentials.
        message = "The server saved the change with warnings; inspect the result before relying on it."
        if strict:
            raise GatewayConfigWarningError(message, code="gateway_config_warning", operation=name)
        warnings.warn(message, GatewayConfigWarning, stacklevel=3)
    if name.startswith(("gateway.provider_credentials.", "gateway.keys.")):
        value = mask_read(value)
    return scrub_management_value(value, secrets)


_PAGE = PaginationSpec("cursor", "items", cursor_param="page", next_cursor_field="next")


def page_data(raw: Any, current: int) -> dict[str, Any]:
    """Convert a DRF page to shared Page data. Never follow a next-link URL."""
    if isinstance(raw, list):
        return {"items": raw, "next": None, "response": raw}
    if not isinstance(raw, Mapping) or not isinstance(raw.get("results"), list):
        raise FutureAGIAPIError(200, None, code="invalid_page", message="Expected DRF results")
    following = None
    link = raw.get("next")
    if isinstance(link, str) and link:
        try:
            values = parse_qs(urlsplit(link).query).get("page", [])
            candidate = int(values[0]) if len(values) == 1 else 0
            if candidate > current:
                following = str(candidate)
        except ValueError:
            pass
    elif "next" not in raw:
        total = raw.get("total_pages")
        if isinstance(total, int) and not isinstance(total, bool) and total > current:
            following = str(current + 1)
    return {"items": raw["results"], "next": following if raw["results"] else None, "response": raw}


class ManagementPage(Page[Any]):
    """A DRF page whose raw body is preserved while iteration walks the shared Page."""
    def __init__(self, data: Any, fetch: Any, seen: frozenset[str] = frozenset()) -> None:
        super().__init__(data, _PAGE, fetch, seen=seen)
        self.raw = data["response"]

    def next_page(self) -> Any:
        if not self.has_more:
            return None
        return ManagementPage(self._fetch(self.next_cursor), self._fetch, self._seen)


class AsyncManagementPage(AsyncPage[Any]):
    """Async twin of ManagementPage."""
    def __init__(self, data: Any, fetch: Any, seen: frozenset[str] = frozenset()) -> None:
        super().__init__(data, _PAGE, fetch, seen=seen)
        self.raw = data["response"]

    async def next_page(self) -> Any:
        if not self.has_more:
            return None
        return AsyncManagementPage(await self._fetch(self.next_cursor), self._fetch, self._seen)


class AsyncManagementResource(Namespace):
    """Async-first management resource sharing policy, errors, retries and raw metadata."""
    async def _call(self, name: str, *, path: Any, query: Any, body: Any, paged: bool = False, strict: bool = False) -> Any:
        validate_body(name, body)
        query = dict(query)
        if paged:
            query.setdefault("page", 1)
        async def request(q: Any) -> Any:
            value, _ = await self._core.call_with_meta(
                name, path=path, query=q, body=body,
                map_response=lambda data, secrets, meta: unwrap(data, name, secrets, meta=meta, strict=strict),
            )
            return value
        raw = await request(query)
        if not paged:
            return raw
        async def fetch(cursor: str) -> Any:
            q = {**query, "page": int(cursor)}
            return page_data(await request(q), int(cursor))
        return AsyncManagementPage(page_data(raw, int(query["page"])), fetch)


class ManagementResource(Namespace):
    """Synchronous twin of AsyncManagementResource."""
    def _call(self, name: str, *, path: Any, query: Any, body: Any, paged: bool = False, strict: bool = False) -> Any:
        validate_body(name, body)
        query = dict(query)
        if paged:
            query.setdefault("page", 1)
        def request(q: Any) -> Any:
            value, _ = self._core.call_with_meta(
                name, path=path, query=q, body=body,
                map_response=lambda data, secrets, meta: unwrap(data, name, secrets, meta=meta, strict=strict),
            )
            return value
        raw = request(query)
        if not paged:
            return raw
        def fetch(cursor: str) -> Any:
            q = {**query, "page": int(cursor)}
            return page_data(request(q), int(cursor))
        return ManagementPage(page_data(raw, int(query["page"])), fetch)
