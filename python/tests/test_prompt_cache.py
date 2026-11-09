"""Behavioral regressions for the prompt cache's background workers."""

import json
from pathlib import Path
import subprocess
import sys
import textwrap


_SOURCE_ROOT = Path(__file__).resolve().parents[1]


def _run_isolated(code):
    # Use this checkout, even when another SDK distribution is installed.
    prelude = """
import json
import sys
import threading

sys.path.insert(0, sys.argv[1])

def deny_network(event, args):
    if event in {"socket.connect", "socket.sendto", "socket.getaddrinfo"}:
        raise AssertionError("Prompt cache tests must not use the network")

sys.addaudithook(deny_network)
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", prelude + textwrap.dedent(code), str(_SOURCE_ROOT)],
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    return json.loads(result.stdout)


def test_importing_fi_prompt_spawns_no_threads():
    started = _run_isolated("""
        before = set(threading.enumerate())
        from fi.prompt import Prompt, PromptTemplate, ModelConfig
        print(json.dumps([t.name for t in threading.enumerate() if t not in before]))
    """)
    assert started == []


def test_constructing_unused_prompt_cache_spawns_no_threads():
    started = _run_isolated("""
        from fi.prompt.cache import PromptCache
        before = set(threading.enumerate())
        cache = PromptCache(max_workers=3)
        print(json.dumps([t.name for t in threading.enumerate() if t not in before]))
    """)
    assert started == []


def test_unused_task_manager_can_shutdown_safely():
    assert _run_isolated("""
        from fi.prompt.cache import _TaskManager
        manager = _TaskManager(2)
        manager._shutdown()
        print(json.dumps(True))
    """) is True


def test_concurrent_first_refreshes_and_repeated_use_share_one_worker_pool():
    result = _run_isolated("""
        from concurrent.futures import ThreadPoolExecutor
        import time
        from fi.prompt import PromptTemplate
        from fi.prompt.cache import PromptCache

        before = set(threading.enumerate())
        cache = PromptCache(max_workers=2)
        template = PromptTemplate(name="fixture")
        barrier = threading.Barrier(8)

        def refresh(index):
            barrier.wait(timeout=5)
            cache.refresh_async(str(index), lambda: template)

        with ThreadPoolExecutor(max_workers=8) as callers:
            list(callers.map(refresh, range(8)))
        deadline = time.monotonic() + 5
        while not all(cache.get(str(i)) is template for i in range(8)):
            assert time.monotonic() < deadline, "Concurrent refreshes did not complete"
            threading.Event().wait(0.01)
        first = {t for t in threading.enumerate()
                 if t not in before and t.name.startswith("PromptCacheWorker")}
        cache.refresh_async("later", lambda: template)
        while cache.get("later") is not template:
            assert time.monotonic() < deadline, "Repeated refresh did not complete"
            threading.Event().wait(0.01)
        second = {t for t in threading.enumerate()
                  if t not in before and t.name.startswith("PromptCacheWorker")}
        print(json.dumps({"workers": len(first), "same_pool": first == second,
                          "refreshed": all(cache.get(str(i)) is template for i in range(8))}))
    """)
    assert result == {"workers": 2, "same_pool": True, "refreshed": True}


def test_duplicate_inflight_refresh_is_coalesced():
    result = _run_isolated("""
        import time
        from fi.prompt import PromptTemplate
        from fi.prompt.cache import PromptCache

        cache = PromptCache(max_workers=1)
        entered, release = threading.Event(), threading.Event()
        calls = []
        template = PromptTemplate(name="fixture")

        def fetch():
            calls.append(1)
            entered.set()
            assert release.wait(5)
            return template

        try:
            cache.refresh_async("key", fetch)
            assert entered.wait(5), "Refresh did not start on demand"
            cache.refresh_async("key", fetch)
        finally:
            release.set()
        deadline = time.monotonic() + 5
        while cache.get("key") is not template:
            assert time.monotonic() < deadline, "Refresh did not populate the cache"
            threading.Event().wait(0.01)
        # A following task on this one-worker pool fences the completed refresh.
        finished = threading.Event()
        cache.refresh_async("fence", lambda: finished.set())
        assert finished.wait(5)
        print(json.dumps(len(calls)))
    """)
    assert result == 1


def test_failed_refresh_can_be_retried():
    result = _run_isolated("""
        import time
        from fi.prompt import PromptTemplate
        from fi.prompt.cache import PromptCache

        cache = PromptCache(max_workers=1)
        template = PromptTemplate(name="fixture")
        calls = []
        finished = threading.Event()

        def fetch():
            calls.append(1)
            if len(calls) == 1:
                raise ValueError("synthetic refresh failure")
            return template

        cache.refresh_async("key", fetch)
        cache.refresh_async("fence", lambda: finished.set())
        assert finished.wait(5), "Worker stopped after a failed refresh"
        cache.refresh_async("key", fetch)
        deadline = time.monotonic() + 5
        while cache.get("key") is not template:
            assert time.monotonic() < deadline, "Failed key could not be retried"
            threading.Event().wait(0.01)
        print(json.dumps(len(calls)))
    """)
    assert result == 2


def test_cache_crud_expiry_stale_fallback_and_keys_are_unchanged():
    assert _run_isolated("""
        from unittest.mock import patch
        from fi.prompt import PromptTemplate
        from fi.prompt.cache import PromptCache

        cache = PromptCache(ttl_sec=10)
        template = PromptTemplate(name="fixture")
        key = cache.make_key("fixture", version="v1", label="ignored")
        assert key == "fixture|v:v1"
        assert cache.make_key("fixture", label="production") == "fixture|label:production"
        assert cache.make_key("fixture") == "fixture"
        assert cache.get("missing") is None
        assert cache.get_stale("missing") is None
        with patch("fi.prompt.cache.time.time", return_value=100):
            cache.set(key, template)
            cache.set("short", template, ttl_sec=1)
        with patch("fi.prompt.cache.time.time", return_value=101):
            assert cache.get(key) is template
            assert cache.get("short") is None
            assert cache.get_stale("short") is template
        with patch("fi.prompt.cache.time.time", return_value=110):
            assert cache.get(key) is None
            assert cache.get_stale(key) is template
        cache.invalidate("fixture|")
        assert cache.get_stale(key) is None
        assert cache.get_stale("short") is template
        print(json.dumps(True))
    """) is True
