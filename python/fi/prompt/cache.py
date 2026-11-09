from __future__ import annotations

import atexit
import copy
import hashlib
import json
import logging
import threading
import time
from queue import Empty, Queue
from typing import Callable, Dict, Optional, Tuple

# We deliberately import via string to avoid circular import at runtime
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from fi.prompt.types import PromptTemplate


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_TTL_SEC = 60 * 5  # 5 minutes
DEFAULT_REFRESH_WORKERS = 2

logger = logging.getLogger("fi.prompt.cache")


# ---------------------------------------------------------------------------
# Internal data structures
# ---------------------------------------------------------------------------


class _CacheItem:
    """A wrapper around the cached PromptTemplate with expiry metadata."""

    __slots__ = ("value", "expiry", "snapshot")

    def __init__(self, value: "PromptTemplate", ttl_sec: int, *, snapshot: bool = False):
        self.snapshot = snapshot
        self.value: "PromptTemplate" = copy.deepcopy(value) if snapshot else value
        self.expiry: float = time.time() + ttl_sec

    def is_stale(self) -> bool:
        return time.time() >= self.expiry


# ---------------------------------------------------------------------------
# Background refresh infra (Queue + workers)
# ---------------------------------------------------------------------------


class _RefreshWorker(threading.Thread):
    """Continuously processes refresh callables from the shared queue."""

    def __init__(self, q: "Queue[Callable[[], None]]", identifier: int):
        super().__init__(daemon=True, name=f"PromptCacheWorker-{identifier}")
        self._queue = q
        self._running = True

    def run(self) -> None:  # noqa: D401 – imperative mood fine
        while self._running:
            try:
                task = self._queue.get(timeout=1)
            except Empty:
                continue  # check _running flag again

            try:
                task()
            except Exception as exc:  # pragma: no cover – log + continue
                logger.warning("Prompt cache refresh task failed: %s", exc, exc_info=True)
            finally:
                self._queue.task_done()

    def stop(self) -> None:
        self._running = False


class _TaskManager:
    """Manages background refresh workers and graceful shutdown."""

    def __init__(self, num_workers: int):
        self._queue: "Queue[Callable[[], None]]" = Queue()
        self._workers = [_RefreshWorker(self._queue, i) for i in range(num_workers)]
        for w in self._workers:
            w.start()

        atexit.register(self._shutdown)

    # Public API -----------------------------------------------------------

    def submit(self, task: Callable[[], None]):
        self._queue.put(task)

    # Private --------------------------------------------------------------

    def _shutdown(self):
        logger.debug("Shutting down PromptCache workers …")
        for w in self._workers:
            w.stop()
        # Drain queue quickly
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except Empty:
                break
        for w in self._workers:
            w.join(timeout=1)
        logger.debug("PromptCache workers shut down.")


# ---------------------------------------------------------------------------
# Public cache API
# ---------------------------------------------------------------------------


class PromptCache:
    """Thread-safe, stale-while-revalidate cache for `PromptTemplate` objects."""

    def __init__(self, ttl_sec: int = DEFAULT_TTL_SEC, max_workers: int = DEFAULT_REFRESH_WORKERS):
        self._ttl_sec = ttl_sec
        self._store: Dict[str, _CacheItem] = {}
        self._lock = threading.Lock()  # protects _store mutations
        self._refreshing_keys: set[str] = set()
        self._tm = _TaskManager(max_workers)

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

    @staticmethod
    def scope_for(client, *, headers: Optional[Dict[str, str]] = None) -> str:
        """Fingerprint the resolved origin and effective authentication/workspace headers."""
        if headers is None:
            headers = client._platform_headers(
                client._base_url + "/", dict(client._default_headers)
            )
        identity = [client._base_url, sorted(
            (name.lower(), value) for name, value in headers.items()
        )]
        return hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()

    @staticmethod
    def make_scoped_key(name: str, *, scope: str, version: Optional[str] = None,
                        label: Optional[str] = None) -> str:
        """Separate authenticated entries from legacy keys without storing header values."""
        selector = [name, version, label if version is None else None]
        return scope + "|" + json.dumps(selector, separators=(",", ":"))

    # ------------------------------- CRUD ------------------------------

    def get(self, key: str) -> Optional["PromptTemplate"]:
        with self._lock:
            item = self._store.get(key)
            if item and not item.is_stale():
                return copy.deepcopy(item.value) if item.snapshot else item.value
            return None

    def get_stale(self, key: str) -> Optional["PromptTemplate"]:
        """Return cached value even if stale (used for fallback)."""
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            return copy.deepcopy(item.value) if item.snapshot else item.value

    def set(self, key: str, template: "PromptTemplate", ttl_sec: Optional[int] = None, *, snapshot: bool = False):
        """Cache a value; snapshots isolate both stored and retrieved templates.

        Direct cache users retain reference semantics unless they opt in.
        """
        if ttl_sec is None:
            ttl_sec = self._ttl_sec
        with self._lock:
            self._store[key] = _CacheItem(template, ttl_sec, snapshot=snapshot)

    def invalidate(self, key_prefix: str):
        with self._lock:
            to_delete = [k for k in self._store if k.startswith(key_prefix)]
            for k in to_delete:
                del self._store[k]

    def invalidate_template(self, name: str):
        """Remove one template's exact key and version/label selector keys."""
        selector_prefixes = (f"{name}|v:", f"{name}|label:")
        with self._lock:
            # Valid template names can contain selector syntax, so keys alone
            # cannot distinguish a selector from a different template's name.
            to_delete = [
                key for key, item in self._store.items()
                if item.value.name == name
                and (key == name or key.startswith(selector_prefixes))
            ]
            for key in to_delete:
                del self._store[key]

    def invalidate_scoped_template(self, name: str, *, scope: str):
        """Evict this identity's selectors, leaving other authenticated scopes intact."""
        prefix = scope + "|"
        with self._lock:
            to_delete = [
                key for key, item in self._store.items()
                if key.startswith(prefix) and item.value.name == name
            ]
            for key in to_delete:
                del self._store[key]
        # Retain cleanup for direct legacy cache users. Public fetches never
        # consume these identity-free entries, and this cannot match scoped keys.
        self.invalidate_template(name)

    # -------------------------- refresh management ---------------------

    def refresh_async(self, key: str, fetch_fn: Callable[[], "PromptTemplate"]):
        """Schedule a refresh if one is not already in-flight."""
        with self._lock:
            if key in self._refreshing_keys:
                return
            self._refreshing_keys.add(key)

        def _task():
            try:
                tpl = fetch_fn()
                self.set(key, tpl)
            finally:
                with self._lock:
                    self._refreshing_keys.discard(key)

        self._tm.submit(_task)


# Global singleton --------------------------------------------------------

prompt_cache = PromptCache() 