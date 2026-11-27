"""The client that ``Dataset.get_dataset_config`` returns sends with the settings of its own call.

The cache of ``Dataset.get_dataset_config`` keeps the dataset config of a lookup. A call served from it gets a
``Dataset`` built from its own arguments and environment: its own keys, base URL, plain http opt-in and session.
These cases read what reached loopback listeners, through the lookup shim of ``test_plain_http_key_guards``
(``api.futureagi.com`` resolves to the loopback interface), with an environment proxy pointed at the proxy
listener, to check that:

* a call that relies on ``FI_ALLOW_INSECURE_HTTP=1`` (argument absent or ``None``) and is served from an entry
  made by a call with ``allow_insecure_http=True`` gets a client whose later keyed request is refused before a
  connection is made once the variable is unset, as a client built directly with the same arguments is;
* the session given to one call (its headers and proxies) does not reach the client of a later call;
* a repeated call is still served from the cache without a new lookup, and a deleted dataset is looked up again.
"""

from __future__ import annotations

import secrets
import uuid

import pytest
from requests_futures.sessions import FuturesSession

from fi.datasets.dataset import Dataset, LRUCache
from fi.datasets.types import DatasetConfig
from tests.test_dataset_config_cache import NAME, DatasetSink
from tests.test_plain_http_key_guards import CODE, net, use_proxy  # noqa: F401

KEY_A = "fikey-tenant-a-" + secrets.token_hex(8)
SECRET_A = "fisec-tenant-a-" + secrets.token_hex(8)
PROBE_HEADER = "X-Session-Probe"


@pytest.fixture(autouse=True)
def empty_cache(monkeypatch):
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=100))


@pytest.fixture
def sink(net, monkeypatch):
    listener = DatasetSink()
    use_proxy(monkeypatch, net)
    yield listener
    listener.close()


def _attempt(call):
    try:
        return call(), None
    except Exception as exc:  # the refusal, or a failure after a request, is what is read
        return None, exc


def _base(listener) -> str:
    return f"http://api.futureagi.com:{listener.port}"


def _counts(listener, proxy) -> tuple:
    return (
        listener.connections,
        listener.key_bytes(KEY_A, SECRET_A),
        proxy.connections,
        proxy.raw.count(KEY_A.encode()) + proxy.raw.count(SECRET_A.encode()),
    )


def _report(listener, proxy) -> str:
    target_c, target_b, proxy_c, proxy_b = _counts(listener, proxy)
    return (
        f"target: {target_c} connections, {target_b} marker bytes, {listener.names_requests} lookups, "
        f"{listener.other_requests} other requests; proxy: {proxy_c} connections, {proxy_b} marker bytes"
    )


def _get_config(base, **kwargs):
    return Dataset.get_dataset_config(NAME, fi_api_key=KEY_A, fi_secret_key=SECRET_A, fi_base_url=base, **kwargs)


# ---------------------------------------------------------------------------------------------
# plain http opt-in from the environment
# ---------------------------------------------------------------------------------------------

env_opt = pytest.mark.parametrize("opt", [{}, {"allow_insecure_http": None}], ids=["opt-in-absent", "opt-in-none"])


@env_opt
def test_client_served_from_an_opted_in_entry_follows_its_own_environment_opt_in(net, sink, monkeypatch, opt):
    base = _base(sink)
    first, error = _attempt(lambda: _get_config(base, allow_insecure_http=True))
    assert error is None and first.dataset_config.id == sink.default_id, (error, _report(sink, net.proxy))

    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    second, error = _attempt(lambda: _get_config(base, **opt))
    assert error is None and second.dataset_config.id == sink.default_id, (error, _report(sink, net.proxy))
    assert sink.names_requests == 1, _report(sink, net.proxy)
    before = _counts(sink, net.proxy)

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP")
    _, error = _attempt(second.delete)

    after = _counts(sink, net.proxy)
    delta = tuple(a - b for a, b in zip(after, before))
    assert delta == (0, 0, 0, 0), (
        f"later delete: target {delta[0]}/{delta[1]}, proxy {delta[2]}/{delta[3]} (connections/marker bytes); "
        f"{_report(sink, net.proxy)}"
    )
    assert getattr(error, "code", None) == CODE, repr(error)


@env_opt
def test_control_client_built_directly_with_the_same_arguments_is_refused(net, sink, monkeypatch, opt):
    config = DatasetConfig(id=uuid.uuid4(), name=NAME, model_type="GenerativeLLM")
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    client = Dataset(dataset_config=config, fi_api_key=KEY_A, fi_secret_key=SECRET_A, fi_base_url=_base(sink), **opt)

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP")
    _, error = _attempt(client.delete)

    counts = _counts(sink, net.proxy)
    assert counts == (0, 0, 0, 0), (
        f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]} (connections/marker bytes)"
    )
    assert getattr(error, "code", None) == CODE, repr(error)


# ---------------------------------------------------------------------------------------------
# session
# ---------------------------------------------------------------------------------------------


def test_session_of_one_call_does_not_reach_the_client_of_a_later_call(net, sink):
    base = _base(sink)
    probe = "probe-" + secrets.token_hex(8)
    session = FuturesSession()
    session.headers[PROBE_HEADER] = probe
    session.proxies = {"http": f"http://127.0.0.1:{net.proxy.port}", "https": f"http://127.0.0.1:{net.proxy.port}"}
    first, error = _attempt(lambda: _get_config(base, allow_insecure_http=True, session=session))
    assert error is None and first.dataset_config.id == sink.default_id, (error, _report(sink, net.proxy))
    probe_before = sink.raw.count(probe.encode())
    assert probe_before > 0, _report(sink, net.proxy)

    second, error = _attempt(lambda: _get_config(base, allow_insecure_http=True))
    assert error is None and second.dataset_config.id == sink.default_id, (error, _report(sink, net.proxy))
    _, error = _attempt(second.delete)

    assert error is None, repr(error)
    deletes = [keys for method, keys, _ in sink.sent if method == "DELETE"]
    assert deletes == [(KEY_A, SECRET_A)], (deletes, _report(sink, net.proxy))
    probe_delta = sink.raw.count(probe.encode()) - probe_before
    assert probe_delta == 0, f"{probe_delta} bytes of the first call's session header at target; {_report(sink, net.proxy)}"
    assert (net.proxy.connections, net.proxy.raw.count(probe.encode())) == (0, 0), _report(sink, net.proxy)
    assert second._session is not session
    assert f"127.0.0.1:{net.proxy.port}" not in str(dict(second._session.proxies or {}))


# ---------------------------------------------------------------------------------------------
# controls: the cache still serves a repeated call, and a deleted dataset is looked up again
# ---------------------------------------------------------------------------------------------


def test_repeated_call_is_served_from_the_cache_with_a_client_of_its_own(net, sink):
    base = _base(sink)
    first, error = _attempt(lambda: _get_config(base, allow_insecure_http=True))
    assert error is None, repr(error)

    second, error = _attempt(lambda: _get_config(base, allow_insecure_http=True))

    assert error is None, repr(error)
    assert sink.names_requests == 1, _report(sink, net.proxy)
    assert second.dataset_config == first.dataset_config
    assert second._default_headers == {"X-Api-Key": KEY_A, "X-Secret-Key": SECRET_A}
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(sink, net.proxy)


def test_dataset_deleted_through_a_served_client_is_looked_up_again(net, sink):
    base = _base(sink)
    first, error = _attempt(lambda: _get_config(base, allow_insecure_http=True))
    assert error is None, repr(error)
    _, error = _attempt(first.delete)
    assert error is None, repr(error)

    again, error = _attempt(lambda: _get_config(base, allow_insecure_http=True))

    assert error is None and again.dataset_config.id == sink.default_id, repr(error)
    assert (sink.names_requests, sink.other_requests) == (2, 1), _report(sink, net.proxy)
    assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0), _report(sink, net.proxy)
