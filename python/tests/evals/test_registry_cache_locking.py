"""Reentrant cache invalidation, including the real autouse-fixture reset helper.

Round 3's plain Lock deadlocks in fixture setup. The production RLock makes
nested clear safe by construction; these tests exercise that helper directly.
"""
import pytest

from fi.evals.core import cloud_registry as registry
from tests.evals._mock_http import reset_caches


@pytest.mark.parametrize("operation", ["reset-helper", "direct-clear"])
def test_clear_under_held_lock_revokes_only_target_cache(monkeypatch, operation):
    for name in ("_RegistryCache", "_PENDING_FILLS", "_CACHE_LOCK"):
        assert getattr(registry, name, None) is not None, f"registry must provide {name}"
    keys = [("http://127.0.0.1:9", name) for name in ("synthetic-a", "synthetic-b")]
    entry = (300.0, {"template": {"name": "template"}})
    cache = registry._RegistryCache({key: entry for key in keys})
    other_cache = registry._RegistryCache({keys[0]: entry})
    other_fill_key = (id(other_cache), keys[0])
    other_token = object()
    pending = {(id(cache), key): object() for key in keys}
    pending[other_fill_key] = other_token
    monkeypatch.setattr(registry, "_CACHE", cache)
    monkeypatch.setattr(registry, "_PENDING_FILLS", pending)

    with registry._CACHE_LOCK:
        # Check reentrancy without blocking before exercising nested clear.
        assert registry._CACHE_LOCK.acquire(blocking=False), "cache lock must be reentrant"
        registry._CACHE_LOCK.release()
        if operation == "reset-helper":
            reset_caches()
        else:
            cache.clear()
        assert cache == {}
        assert pending == {other_fill_key: other_token}
        assert other_cache == {keys[0]: entry}
