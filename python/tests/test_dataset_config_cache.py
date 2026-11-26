"""The dataset-config cache of ``Dataset.get_dataset_config`` and the keyed requests sent after it.

``Dataset.get_dataset_config`` keeps the dataset config it looks up, so a later call for the same dataset name
with the same keys, base URL and plain http opt-in can reuse it; each call gets a ``Dataset`` built from its own
arguments and environment. These cases read what reached loopback listeners, through the lookup shim of
``test_plain_http_key_guards`` (``api.futureagi.com`` and ``plain.example.test`` resolve to the loopback
interface), to check that:

* a call that does not opt in to plain http is refused before a connection is made, even after an opted-in call
  for the same dataset;
* a call with other keys sends its own request with its own keys and gets its own config;
* a call with another base URL sends its own request to its own base URL;
* a repeated call with the same keys, base URL and opt-in is still served without a new request.
"""

from __future__ import annotations

import json
import secrets
import socket
import time
import uuid
from urllib.parse import parse_qs, urlparse

import pytest

from fi.datasets.dataset import Dataset, LRUCache
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, Sink, _marker_forms, net, use_proxy  # noqa: F401

KEY_B = "fikey-tenant-b-" + secrets.token_hex(6)
SECRET_B = "fisec-tenant-b-" + secrets.token_hex(6)
NAME = "cache-probe"
NAMES_PATH = "/model-hub/develops/get-datasets-names/"


def _header(head: bytes, name: str) -> str | None:
    for line in head.split(b"\r\n")[1:]:
        field, _, value = line.partition(b":")
        if field.strip().lower() == name.lower().encode():
            return value.strip().decode("latin-1")
    return None


class DatasetSink(Sink):
    """A loopback listener that answers the dataset-names lookup with one dataset of the requested name.

    The dataset id depends on the keys the request carries (``ids``), else it is ``default_id``, so a caller can
    tell whose config it received."""

    def __init__(self, ids: dict | None = None) -> None:
        self.ids = ids or {}
        self.default_id = uuid.uuid4()
        self.names_requests = 0
        self.other_requests = 0
        self.sent: list = []
        super().__init__()

    def _handle(self, conn: socket.socket) -> None:
        conn.settimeout(0.4)
        data = b""
        try:
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            head, _, body = data.partition(b"\r\n\r\n")
            length = int(_header(head, "Content-Length") or 0)
            while len(body) < length:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                body += chunk
            parts = head.split(b"\r\n", 1)[0].split(b" ")
            keys = (_header(head, "X-Api-Key"), _header(head, "X-Secret-Key"))
            with self._lock:
                self.raw += head + b"\r\n\r\n" + body
                self.sent.append((parts[0].decode("latin-1"), keys, body.decode("latin-1")))
            target = parts[1].decode("latin-1") if len(parts) > 1 else "/"
            path = urlparse(target).path
            if path == NAMES_PATH:
                with self._lock:
                    self.names_requests += 1
                name = parse_qs(urlparse(target).query).get("search_text", [NAME])[0]
                dataset_id = self.ids.get(keys, self.default_id)
                body = {"result": {"datasets": [{"datasetId": str(dataset_id), "name": name, "modelType": "GenerativeLLM"}]}}
            else:
                with self._lock:
                    self.other_requests += 1
                body = {"status": True, "result": {}}
            payload = json.dumps(body).encode()
            conn.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                + str(len(payload)).encode()
                + b"\r\nConnection: close\r\n\r\n"
                + payload
            )
        except OSError:
            pass
        finally:
            conn.close()

    def key_bytes(self, *values: str) -> int:
        time.sleep(0.15)
        with self._lock:
            raw = self.raw
        return sum(raw.count(form) for form in _marker_forms(*values))


@pytest.fixture(autouse=True)
def empty_cache(monkeypatch):
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=100))


@pytest.fixture
def one(net, monkeypatch):
    """A dataset listener behind ``api.futureagi.com`` with an environment proxy set to the proxy listener."""
    sink = DatasetSink()
    use_proxy(monkeypatch, net)
    yield sink
    sink.close()


@pytest.fixture
def two(net, monkeypatch):
    """Two dataset listeners, behind ``api.futureagi.com`` and ``plain.example.test``, and an environment proxy."""
    first, second = DatasetSink(), DatasetSink()
    use_proxy(monkeypatch, net)
    yield first, second
    first.close()
    second.close()


def _base(host: str, sink: Sink) -> str:
    return f"http://{host}:{sink.port}"


def _attempt(call):
    try:
        return call(), None
    except Exception as exc:  # the refusal, or a failure after a request, is what is read
        return None, exc


def _counts(sink: DatasetSink, proxy: Sink, api_key: str = KEY, secret_key: str = SECRET):
    return (sink.connections, sink.key_bytes(api_key, secret_key), proxy.connections, proxy.marker_bytes())


def _report(sink: DatasetSink, proxy: Sink) -> str:
    return (
        f"target: {sink.connections} connections, {sink.key_bytes(KEY, SECRET)} bytes of key A, "
        f"{sink.key_bytes(KEY_B, SECRET_B)} bytes of key B, {sink.names_requests} lookups, "
        f"{sink.other_requests} other requests; proxy: {proxy.connections} connections, "
        f"{proxy.marker_bytes()} marker bytes"
    )


def _get_config(base, api_key, secret_key, **opt):
    return Dataset.get_dataset_config(NAME, fi_api_key=api_key, fi_secret_key=secret_key, fi_base_url=base, **opt)


def _delete_dataset(base, api_key, secret_key, **opt):
    return Dataset.delete_dataset(NAME, fi_api_key=api_key, fi_secret_key=secret_key, fi_base_url=base, **opt)


OPERATIONS = {"get-dataset-config": _get_config, "delete-dataset": _delete_dataset}
operations = pytest.mark.parametrize("operation", list(OPERATIONS), ids=list(OPERATIONS))
second_opt = pytest.mark.parametrize(
    "opt",
    [{"allow_insecure_http": False}, {}, {"allow_insecure_http": None}],
    ids=["opt-in-false", "opt-in-absent", "opt-in-none"],
)


# ---------------------------------------------------------------------------------------------
# plain http opt-in
# ---------------------------------------------------------------------------------------------


@operations
@second_opt
def test_call_without_opt_in_after_opted_in_call_is_refused(net, one, operation, opt):
    base = _base("api.futureagi.com", one)
    first, error = _attempt(lambda: _get_config(base, KEY, SECRET, allow_insecure_http=True))
    assert error is None and first.dataset_config.id == one.default_id, (error, _report(one, net.proxy))
    before = _counts(one, net.proxy)
    assert before[0] == 1 and before[1] > 0 and before[2:] == (0, 0), _report(one, net.proxy)

    _, error = _attempt(lambda: OPERATIONS[operation](base, KEY, SECRET, **opt))

    assert _counts(one, net.proxy) == before, _report(one, net.proxy)
    assert getattr(error, "code", None) == CODE, repr(error)


@second_opt
def test_call_without_opt_in_is_refused_with_the_plain_http_code(net, one, opt):
    _, error = _attempt(lambda: _get_config(_base("api.futureagi.com", one), KEY, SECRET, **opt))

    assert _counts(one, net.proxy) == (0, 0, 0, 0), _report(one, net.proxy)
    assert getattr(error, "code", None) == CODE, repr(error)


# ---------------------------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------------------------

KEY_PAIRS = {
    "both-keys-differ": (KEY_B, SECRET_B),
    "api-key-differs": (KEY_B, SECRET),
    "secret-key-differs": (KEY, SECRET_B),
}
key_pairs = pytest.mark.parametrize("pair", list(KEY_PAIRS), ids=list(KEY_PAIRS))


@key_pairs
def test_call_with_other_keys_sends_its_own_lookup_and_gets_its_own_config(net, pair):
    api_b, secret_b = KEY_PAIRS[pair]
    id_a, id_b = uuid.uuid4(), uuid.uuid4()
    sink = DatasetSink(ids={(KEY, SECRET): id_a, (api_b, secret_b): id_b})
    try:
        base = _base("api.futureagi.com", sink)
        a, error = _attempt(lambda: _get_config(base, KEY, SECRET, allow_insecure_http=True))
        assert error is None and a.dataset_config.id == id_a, (error, _report(sink, net.proxy))
        only_a = [value for value in (KEY, SECRET) if value not in (api_b, secret_b)]
        before = {value: sink.key_bytes(value) for value in {KEY, SECRET, api_b, secret_b}}

        b, error = _attempt(lambda: _get_config(base, api_b, secret_b, allow_insecure_http=True))

        assert error is None, repr(error)
        assert (sink.connections, sink.names_requests) == (2, 2), _report(sink, net.proxy)
        assert [sink.key_bytes(value) - before[value] for value in only_a] == [0] * len(only_a), _report(sink, net.proxy)
        assert sink.key_bytes(api_b) > before[api_b] and sink.key_bytes(secret_b) > before[secret_b], _report(sink, net.proxy)
        assert b is not a and b.dataset_config.id == id_b, (b.dataset_config if b else None, _report(sink, net.proxy))
        assert b._default_headers == {"X-Api-Key": api_b, "X-Secret-Key": secret_b}
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(sink, net.proxy)
    finally:
        sink.close()


def test_other_tenant_delete_carries_only_its_own_keys(net):
    id_a, id_b = uuid.uuid4(), uuid.uuid4()
    sink = DatasetSink(ids={(KEY, SECRET): id_a, (KEY_B, SECRET_B): id_b})
    try:
        base = _base("api.futureagi.com", sink)
        _, error = _attempt(lambda: _get_config(base, KEY, SECRET, allow_insecure_http=True))
        assert error is None, repr(error)
        a_bytes = sink.key_bytes(KEY, SECRET)

        _, error = _attempt(lambda: _delete_dataset(base, KEY_B, SECRET_B, allow_insecure_http=True))

        assert error is None, repr(error)
        assert sink.key_bytes(KEY, SECRET) == a_bytes, _report(sink, net.proxy)
        assert sink.key_bytes(KEY_B, SECRET_B) > 0, _report(sink, net.proxy)
        assert (sink.names_requests, sink.other_requests) == (2, 1), _report(sink, net.proxy)
        deletes = [(keys, body) for method, keys, body in sink.sent if method == "DELETE"]
        assert deletes == [((KEY_B, SECRET_B), json.dumps({"dataset_ids": [str(id_b)]}))], deletes
    finally:
        sink.close()


# ---------------------------------------------------------------------------------------------
# base URL
# ---------------------------------------------------------------------------------------------


@operations
def test_call_with_other_base_url_sends_to_its_own_base_url(net, two, operation):
    first, second = two
    base_1, base_2 = _base("api.futureagi.com", first), _base("plain.example.test", second)
    a, error = _attempt(lambda: _get_config(base_1, KEY, SECRET, allow_insecure_http=True))
    assert error is None and a.dataset_config.id == first.default_id, (error, _report(first, net.proxy))
    first_before = _counts(first, net.proxy)

    b, error = _attempt(lambda: OPERATIONS[operation](base_2, KEY, SECRET, allow_insecure_http=True))

    assert error is None, repr(error)
    assert _counts(first, net.proxy) == first_before, _report(first, net.proxy)
    assert second.names_requests == 1 and second.key_bytes(KEY, SECRET) > 0, _report(second, net.proxy)
    if operation == "delete-dataset":
        deletes = [(keys, body) for method, keys, body in second.sent if method == "DELETE"]
        assert deletes == [((KEY, SECRET), json.dumps({"dataset_ids": [str(second.default_id)]}))], deletes
    else:
        assert b is not a and b.dataset_config.id == second.default_id and b._base_url == base_2
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(second, net.proxy)


# ---------------------------------------------------------------------------------------------
# controls: the cache still serves a repeated call with the same keys, base URL and opt-in
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("excluded", [None, ["other"]], ids=["no-exclusions", "with-exclusions"])
def test_repeated_call_with_same_client_settings_is_served_from_the_cache(net, one, excluded):
    base = _base("api.futureagi.com", one)
    a, error = _attempt(lambda: Dataset.get_dataset_config(
        NAME, excluded, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, allow_insecure_http=True,
    ))
    assert error is None, repr(error)
    before = _counts(one, net.proxy)

    b, error = _attempt(lambda: Dataset.get_dataset_config(
        NAME, excluded, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, allow_insecure_http=True,
    ))

    assert error is None, repr(error)
    assert b is not a and b.dataset_config == a.dataset_config
    assert _counts(one, net.proxy) == before, _report(one, net.proxy)


@pytest.mark.parametrize("excluded", [None, ["other"]], ids=["no-exclusions", "with-exclusions"])
def test_opted_in_lookup_is_sent_directly_past_the_environment_proxy(net, one, excluded):
    a, error = _attempt(
        lambda: Dataset.get_dataset_config(
            NAME, excluded, fi_api_key=KEY, fi_secret_key=SECRET,
            fi_base_url=_base("api.futureagi.com", one), allow_insecure_http=True,
        )
    )

    assert error is None and a.dataset_config.id == one.default_id, repr(error)
    assert one.connections == 1 and one.key_bytes(KEY, SECRET) > 0, _report(one, net.proxy)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(one, net.proxy)
