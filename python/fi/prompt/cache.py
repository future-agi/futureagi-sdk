from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional

# We deliberately import via string to avoid circular import at runtime
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from fi.prompt.types import PromptTemplate


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_TTL_SEC = 60 * 5  # 5 minutes

logger = logging.getLogger("fi.prompt.cache")


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


class _CacheItem:
    """A wrapper around the cached PromptTemplate with expiry metadata."""

    __slots__ = ("value", "expiry")

    def __init__(self, value: "PromptTemplate", ttl_sec: int):
        self.value: "PromptTemplate" = value
        self.expiry: float = time.time() + ttl_sec

    def is_stale(self) -> bool:
        return time.time() >= self.expiry


# ---------------------------------------------------------------------------
# Public cache API
# ---------------------------------------------------------------------------


class PromptCache:
    """Thread-safe, stale-while-revalidate cache for `PromptTemplate` objects."""

    def __init__(self, ttl_sec: int = DEFAULT_TTL_SEC):
        self._ttl_sec = ttl_sec
        self._store: Dict[str, _CacheItem] = {}
        self._lock = threading.Lock()  # protects _store mutations

    # ------------------------------- helpers ----------------------------

    @staticmethod
    def make_key(name: str, *, version: Optional[str] = None, label: Optional[str] = None) -> str:
        """Create deterministic cache key."""
        parts = [name]
        if version is not None:
            parts.append(f"v:{version}")
        elif label is not None:
            parts.append(f"label:{label}")
        return "|".join(parts)

    # ------------------------------- CRUD ------------------------------

    def get(self, key: str) -> Optional["PromptTemplate"]:
        with self._lock:
            item = self._store.get(key)
            if item and not item.is_stale():
                return item.value
            return None

    def get_stale(self, key: str) -> Optional["PromptTemplate"]:
        """Return cached value even if stale (used for fallback)."""
        with self._lock:
            item = self._store.get(key)
            return item.value if item else None

    def set(self, key: str, template: "PromptTemplate", ttl_sec: Optional[int] = None):
        if ttl_sec is None:
            ttl_sec = self._ttl_sec
        with self._lock:
            self._store[key] = _CacheItem(template, ttl_sec)

    def invalidate(self, key_prefix: str):
        with self._lock:
            to_delete = [k for k in self._store if k.startswith(key_prefix)]
            for k in to_delete:
                del self._store[k]


# Global singleton --------------------------------------------------------

prompt_cache = PromptCache()
