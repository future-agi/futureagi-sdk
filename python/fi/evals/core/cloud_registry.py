"""
Cloud eval registry — source of truth for eval metadata.

Fetches the full template list from `/sdk/api/v1/get-evals/` and briefly caches
successful results by normalized base URL and a full-credential digest. Exposes helpers that
turn user-supplied kwargs into the exact key set the backend will accept,
so the SDK never drifts from the backend when evals are added/renamed.

Why this exists
---------------

The old ``templates.py`` hardcoded Pydantic Input models per template
(``OutputOnly``, ``OutputWithContext``, ``OutputWithExpected``, ...). The
Turing revamp renamed/removed/replaced ~50 templates; the hardcoded
schemas drifted and 28 of 57 stopped working. Going forward, the backend
is authoritative — the SDK reads ``required_keys`` and sends only those.
"""
from __future__ import annotations

import hashlib
import logging
import threading
from time import monotonic
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

log = logging.getLogger(__name__)


# Both module and borrowed-session caches hold (expires_at, registry) entries.
# Keys retain only the normalized base URL and a one-way credential digest.
CACHE_TTL_SECONDS = 300
# Cache-reset callers may already hold this lock when invoking clear().
_CACHE_LOCK = threading.RLock()
# Only the latest in-flight fill for a cache/key may publish. Cache identity
# isolates borrowed sessions; active calls retain the cache, preventing id reuse.
_PENDING_FILLS: Dict[Tuple[int, Tuple[str, str]], object] = {}


def _invalidate_cache(cache: dict) -> None:
    """Clear entries and revoke all fills for this cache; caller holds _CACHE_LOCK."""
    dict.clear(cache)
    for fill_key in list(_PENDING_FILLS):
        if fill_key[0] == id(cache):
            del _PENDING_FILLS[fill_key]


class _RegistryCache(dict):
    def clear(self) -> None:
        with _CACHE_LOCK:
            _invalidate_cache(self)


_CACHE: Dict[Tuple[str, str], Tuple[float, Dict[str, Dict[str, Any]]]] = _RegistryCache()

# Aliases user kwargs can use → canonical backend keys.
# Maps are checked in order; first match wins.
_KEY_ALIASES: Dict[str, Tuple[str, ...]] = {
    # Bidirectional output↔input — some evals only accept one of the two
    # (e.g. prompt_injection wants `input`, toxicity wants `output`).
    # Aliasing only fires when the canonical key isn't already in user_inputs,
    # so we can't accidentally overwrite an explicit user value.
    "output": ("output", "response", "answer", "generated", "input"),
    "input": ("input", "query", "question", "prompt_input", "output"),
    "context": ("context", "contexts"),
    "expected": ("expected", "expected_output", "expected_response", "ground_truth"),
    "expected_value": ("expected_value", "expected_output", "expected_response", "ground_truth"),
    "generated_value": ("generated_value", "output", "response", "answer"),
    "reference": ("reference", "expected_output", "expected_response", "ground_truth"),
    "hypothesis": ("hypothesis", "output", "response"),
    "text": ("text", "output", "content"),
    "conversation": ("conversation", "messages"),
    "prompt": ("prompt", "instructions", "system_prompt"),
    "system_prompt": ("system_prompt", "prompt", "instructions"),
    "image": ("image", "image_url", "input_image_url"),
    "caption": ("caption", "output"),
    "instruction": ("instruction", "prompt"),
    "instructions": ("instructions", "prompt"),
    "images": ("images", "image_urls", "input_image_urls"),
    "input_pdf": ("input_pdf", "pdf"),
    "json_content": ("json_content", "json", "expected_output"),
    "input_audio": ("input_audio", "audio"),
    "audio": ("audio", "input_audio"),
    "generated_audio": ("generated_audio", "audio", "output"),
    "generated_transcript": ("generated_transcript", "transcript", "output"),
}


def _cache_key(
    base_url: str, api_key: Optional[str], secret_key: Optional[str]
) -> Tuple[str, str]:
    digest = hashlib.sha256()
    for value in (api_key or "", secret_key or ""):
        encoded = value.encode("utf-8")
        # Length framing is unambiguous even if a credential contains a separator.
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return (base_url.rstrip("/"), digest.hexdigest())


def load_registry(
    base_url: str,
    api_key: Optional[str],
    secret_key: Optional[str],
    *,
    force_refresh: bool = False,
    session: Any = None,
) -> Dict[str, Dict[str, Any]]:
    """Fetch and cache the eval template list. Returns {eval_name: info}."""
    key = _cache_key(base_url, api_key, secret_key)
    cache = _CACHE if session is None else session.registry_cache
    with _CACHE_LOCK:
        if session is not None and getattr(session, "closed", False):
            _invalidate_cache(cache)
            return {}
        cached = cache.get(key)
        if not force_refresh and cached is not None and monotonic() < cached[0]:
            return cached[1]
        if force_refresh or cached is not None:
            _invalidate_cache(cache)
        # A plain miss supersedes only an older fill for the same key.
        fill_key = (id(cache), key)
        token = object()
        _PENDING_FILLS[fill_key] = token

    url = f"{base_url.rstrip('/')}/sdk/api/v1/get-evals/"
    headers = {}
    if api_key:
        headers["X-Api-Key"] = api_key
    if secret_key:
        headers["X-Secret-Key"] = secret_key

    try:
        # Imported lazily to avoid a circular import at module load time.
        import requests

        resp = (requests.get(url, headers=headers, timeout=30) if session is None
                else session.get(url, headers=headers))
        resp.raise_for_status()
        if not 200 <= resp.status_code < 300:
            raise ValueError("cloud eval registry request was not successful")
        body = resp.json()
        if not isinstance(body, dict) or body.get("status") is False:
            raise ValueError("cloud eval registry response was not successful")
        items = body.get("result")
        if not isinstance(items, list):
            raise ValueError("invalid cloud eval registry result")
        by_name: Dict[str, Dict[str, Any]] = {}
        for item in items:
            name = item.get("name")
            if name:
                by_name[name] = item
        with _CACHE_LOCK:
            if _PENDING_FILLS.get(fill_key) is token:
                cache[key] = (monotonic() + CACHE_TTL_SECONDS, by_name)
    except Exception as exc:
        with _CACHE_LOCK:
            # Even an older request's rejection revokes every cached or pending
            # success for this cache: the next call must authenticate again.
            _invalidate_cache(cache)
        log.warning("Failed to load cloud eval registry from %s; error type: %s", url, type(exc).__name__)
        return {}
    finally:
        with _CACHE_LOCK:
            # Do not discard a replacement token belonging to another request.
            if _PENDING_FILLS.get(fill_key) is token:
                _PENDING_FILLS.pop(fill_key, None)
    log.debug("Loaded %d cloud eval templates from %s", len(by_name), url)
    return by_name


def get_template_info(
    name: str,
    *,
    base_url: str,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    session: Any = None,
) -> Optional[Dict[str, Any]]:
    """Return the backend's config block for a given eval, or None."""
    reg = load_registry(base_url, api_key, secret_key, session=session)
    return reg.get(name)


def get_required_keys(
    name: str,
    *,
    base_url: str,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    session: Any = None,
) -> List[str]:
    """List the keys the backend requires for this eval. Empty list if unknown."""
    info = get_template_info(name, base_url=base_url, api_key=api_key, secret_key=secret_key, session=session)
    if not info:
        return []
    return list(info.get("config", {}).get("required_keys", []) or [])


def map_inputs_to_backend(
    name: str,
    user_inputs: Dict[str, Any],
    *,
    base_url: str,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    session: Any = None,
) -> Dict[str, Any]:
    """
    Produce the exact payload the backend expects for ``eval_name``, by:
      1. Looking up the eval's required_keys from the cached registry.
      2. Taking each required key from user_inputs directly if present.
      3. Otherwise resolving via known aliases (e.g. ``output`` → ``response``).
      4. Dropping any keys the backend doesn't accept (the api is strict).

    If the eval isn't in the registry (unknown name, registry load failed),
    falls back to passing user_inputs through unmodified so the backend
    can return its own validation error.
    """
    required = get_required_keys(
        name, base_url=base_url, api_key=api_key, secret_key=secret_key, session=session
    )
    if not required:
        return dict(user_inputs)

    mapped: Dict[str, Any] = {}
    for key in required:
        if key in user_inputs:
            mapped[key] = user_inputs[key]
            continue
        for alias in _KEY_ALIASES.get(key, ()):
            if alias in user_inputs and alias != key:
                mapped[key] = user_inputs[alias]
                break
    return mapped


def list_known_names(
    *,
    base_url: str,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    session: Any = None,
) -> Set[str]:
    """Names of all evals the backend currently has registered."""
    return set(load_registry(base_url, api_key, secret_key, session=session).keys())
