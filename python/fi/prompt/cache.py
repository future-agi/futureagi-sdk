from __future__ import annotations

import atexit
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

    __slots__ = ("value", "expiry")

    def __init__(self, value: "PromptTemplate", ttl_sec: int):
        self.value: "PromptTemplate" = value
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