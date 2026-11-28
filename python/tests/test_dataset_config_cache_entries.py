"""Entries of the ``Dataset.get_dataset_config`` cache hold dataset configs, not clients.

Each entry is keyed by the dataset name, the exclusions and a digest of the base URL, keys and effective headers, and holds the dataset config of the lookup, so a later call that computes the same key sends
with its own keys and to its own base URL. These cases change the
environment while a lookup is in flight (the listener does it on its first request, the way another thread
could), plant an entry whose client differs from its key, and build clients of another tenant on other threads
while lookups run, then read what reached the loopback listeners and what the cache holds.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid

import pytest

from fi.datasets.dataset import Dataset, LRUCache
from fi.datasets.types import DatasetConfig
from tests.test_dataset_config_cache import KEY_B, NAME, SECRET_B, DatasetSink, opted_in  # noqa: F401
from tests.test_plain_http_key_guards import KEY, SECRET, net, use_proxy  # noqa: F401


@pytest.fixture(autouse=True)
def empty_cache(monkeypatch):
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=1000))


class SwitchingSink(DatasetSink):
    """A dataset listener that calls ``on_first`` when its first request arrives, before it answers."""

    def __init__(self, on_first, ids: dict | None = None) -> None:
        self._on_first = on_first
        self._fired = False
        super().__init__(ids=ids)

    def _handle(self, conn) -> None:
        with self._lock:
            fire, self._fired = not self._fired, True
        if fire:
            self._on_first()
        super()._handle(conn)


def _mismatched_entries() -> list:
    """Entries that hold anything other than a dataset config: a client kept in the cache would carry the keys,
    base URL, opt-in and session it was built with to a later call."""
    return [
        (key[1], key[0], type(value).__name__)
        for key, value in list(Dataset._dataset_instance_cache.cache.items())
        if not isinstance(value, DatasetConfig)
    ]


def _deletes(sink: DatasetSink) -> list:
    return [(keys, body) for method, keys, body in list(sink.sent) if method == "DELETE"]


def _body(dataset_id) -> str:
    return json.dumps({"dataset_ids": [str(dataset_id)]})


def test_environment_keys_changed_during_a_lookup_do_not_reach_a_later_call(net, monkeypatch, opted_in):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_API_KEY", KEY)
    monkeypatch.setenv("FI_SECRET_KEY", SECRET)
    id_a = uuid.uuid4()
    sink = SwitchingSink(
        lambda: os.environ.update(FI_API_KEY=KEY_B, FI_SECRET_KEY=SECRET_B), ids={(KEY, SECRET): id_a}
    )
    try:
        base = f"http://plain.example.test:{sink.port}"
        first = Dataset.get_dataset_config(NAME, fi_base_url=base)
        assert first.dataset_config.id == id_a

        later = Dataset.get_dataset_config(
            NAME, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base
        )
        Dataset.delete_dataset(NAME, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base)

        assert (sink.connections, sink.key_bytes(KEY_B, SECRET_B)) == (2, 0), sink.sent
        assert _deletes(sink) == [((KEY, SECRET), _body(id_a))]
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0)
        assert later._default_headers == {"X-Api-Key": KEY, "X-Secret-Key": SECRET}
        assert _mismatched_entries() == []
    finally:
        sink.close()


def test_environment_base_url_changed_during_a_lookup_does_not_redirect_a_later_call(net, monkeypatch, opted_in):
    use_proxy(monkeypatch, net)
    other = DatasetSink()
    sink = SwitchingSink(lambda: os.environ.update(FI_BASE_URL=f"http://127.0.0.1:{other.port}"))
    try:
        base = f"http://plain.example.test:{sink.port}"
        monkeypatch.setenv("FI_BASE_URL", base)
        first = Dataset.get_dataset_config(NAME, fi_api_key=KEY, fi_secret_key=SECRET)
        assert first.dataset_config.id == sink.default_id
        os.environ["FI_BASE_URL"] = base

        Dataset.delete_dataset(NAME, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base)

        assert (other.connections, other.key_bytes(KEY, SECRET)) == (0, 0), other.sent
        assert _deletes(sink) == [((KEY, SECRET), _body(sink.default_id))]
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0)
        assert _mismatched_entries() == []
    finally:
        sink.close()
        other.close()


def test_entry_whose_client_differs_from_its_key_cannot_send(net, monkeypatch, opted_in):
    use_proxy(monkeypatch, net)
    id_a, id_b = uuid.uuid4(), uuid.uuid4()
    sink = DatasetSink(ids={(KEY, SECRET): id_a})
    try:
        base = f"http://plain.example.test:{sink.port}"
        tenant_a = Dataset(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base)
        planted = Dataset(
            dataset_config=DatasetConfig(id=id_b, name=NAME, model_type="GenerativeLLM"),
            fi_api_key=KEY_B,
            fi_secret_key=SECRET_B,
            fi_base_url=base,
        )
        scope = Dataset._config_cache_scope(tenant_a)
        assert scope is not None
        cache_key = (scope, NAME, ())
        cache = Dataset._dataset_instance_cache
        cache.put(cache_key, planted)
        kwargs = dict(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base)

        got = Dataset.get_dataset_config(NAME, **kwargs)
        assert got is not planted and got._default_headers == {"X-Api-Key": KEY, "X-Secret-Key": SECRET}
        with pytest.raises(AttributeError, match="has no attribute 'id'"):
            got.delete()
        with pytest.raises(AttributeError, match="has no attribute 'id'"):
            Dataset.delete_dataset(NAME, **kwargs)

        assert sink.key_bytes(KEY_B, SECRET_B) == 0, sink.sent
        assert (sink.connections, sink.names_requests, sink.key_bytes(KEY, SECRET)) == (0, 0, 0), sink.sent
        assert _deletes(sink) == []
        net.nothing_sent()

        cache.evict(lambda key: key == cache_key)
        got = Dataset.get_dataset_config(NAME, **kwargs)
        Dataset.delete_dataset(NAME, **kwargs)

        assert sink.key_bytes(KEY_B, SECRET_B) == 0, sink.sent
        assert (sink.names_requests, sink.key_bytes(KEY, SECRET) > 0) == (1, True), sink.sent
        assert _deletes(sink) == [((KEY, SECRET), _body(id_a))]
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0)
        assert got is not planted and got.dataset_config.id == id_a
        assert _mismatched_entries() == []
    finally:
        sink.close()


def test_entries_built_while_another_tenant_builds_clients_match_their_keys(net, monkeypatch, opted_in):
    """Smoke case: tenant B builds clients on other threads while tenant A's lookups run. Every entry matches its
    own key, and tenant A's later calls with its own keys carry only those keys."""
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_API_KEY", KEY)
    monkeypatch.setenv("FI_SECRET_KEY", SECRET)
    sink = DatasetSink()
    base = f"http://plain.example.test:{sink.port}"
    names = [f"{NAME}-{index}" for index in range(300)]
    stop = threading.Event()

    def tenant_b() -> None:
        while not stop.is_set():
            Dataset(fi_api_key=KEY_B, fi_secret_key=SECRET_B, fi_base_url=base)

    interval = sys.getswitchinterval()
    threads = [threading.Thread(target=tenant_b, daemon=True) for _ in range(3)]
    try:
        sys.setswitchinterval(1e-6)
        for thread in threads:
            thread.start()
        for name in names:
            try:
                Dataset.get_dataset_config(name, fi_base_url=base)
            except Exception:  # a lookup sent with mixed keys may fail; what the cache keeps is what is read
                pass
    finally:
        stop.set()
        for thread in threads:
            thread.join()
        sys.setswitchinterval(interval)
    try:
        mismatched = _mismatched_entries()
        before = sink.key_bytes(KEY_B, SECRET_B)
        sent_before = len(sink.sent)

        for name in names:
            Dataset.delete_dataset(name, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base)

        assert sink.key_bytes(KEY_B, SECRET_B) == before
        later = list(sink.sent)[sent_before:]
        assert {keys for _, keys, _ in later} == {(KEY, SECRET)}
        assert len([1 for method, _, _ in later if method == "DELETE"]) == len(names)
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0)
        assert mismatched == []
    finally:
        sink.close()
