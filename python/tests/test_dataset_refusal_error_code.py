"""The error code a ``DatasetError`` reports when ``fi.datasets`` raises it in place of a plain http refusal.

``fi.datasets`` wraps a refused request in ``DatasetError``; that error carries ``.code`` ``insecure_http_origin``,
and ``get_error_code()`` reports the same code. A ``DatasetError`` raised for any other reason keeps its own code.

Every case targets loopback listeners through the lookup shim of ``test_plain_http_key_guards``
(``api.futureagi.com`` resolves to the loopback interface), with an environment proxy pointed at the proxy
listener, and reads the connections and marker bytes that reached each listener, so no case reaches a real host.
"""

from __future__ import annotations

import socket

import pytest

from fi.datasets.dataset import Dataset, LRUCache
from fi.datasets.types import Column, DatasetConfig, ModelTypes
from fi.utils.errors import DatasetError, DatasetNotFoundError
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, net, use_proxy  # noqa: F401

DATASET_CODE = "DATASET_OPERATION_INVALID"
NAME = "refusal-code-probe"


@pytest.fixture(autouse=True)
def empty_dataset_cache(monkeypatch):
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=100))


def _attempt(call):
    try:
        return call(), None
    except Exception as exc:  # the raised error is what is read
        return None, exc


def _counts(net) -> tuple:
    return (net.target.connections, net.target.marker_bytes(), net.proxy.connections, net.proxy.marker_bytes())


def _keys() -> dict:
    return {"fi_api_key": KEY, "fi_secret_key": SECRET}


CALLS = {
    "dataset-by-name": lambda base, **opt: Dataset(
        dataset_config=DatasetConfig(name=NAME, model_type=ModelTypes.GENERATIVE_LLM), fi_base_url=base, **_keys(), **opt
    ),
    "get-dataset-config": lambda base, **opt: Dataset.get_dataset_config(NAME, fi_base_url=base, **_keys(), **opt),
    "download-dataset": lambda base, **opt: Dataset.download_dataset(NAME, fi_base_url=base, **_keys(), **opt),
    "delete-dataset": lambda base, **opt: Dataset.delete_dataset(NAME, fi_base_url=base, **_keys(), **opt),
    "add-dataset-columns": lambda base, **opt: Dataset.add_dataset_columns(
        NAME, [Column(name="c", data_type="text")], fi_base_url=base, **_keys(), **opt
    ),
}
calls = pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
opts = pytest.mark.parametrize(
    "opt", [{}, {"allow_insecure_http": None}, {"allow_insecure_http": False}], ids=["absent", "none", "false"]
)


@calls
@opts
def test_refused_dataset_call_reports_the_refusal_code(net, monkeypatch, call, opt):
    use_proxy(monkeypatch, net)

    _, error = _attempt(lambda: CALLS[call](f"http://api.futureagi.com:{net.target.port}", **opt))

    counts = _counts(net)
    assert counts == (0, 0, 0, 0), f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]}"
    assert isinstance(error, DatasetError), repr(error)
    assert getattr(error, "code", None) == CODE, f"{type(error).__name__}: {error}"
    assert error.get_error_code() == CODE, (
        f"get_error_code()={error.get_error_code()!r}, .code={getattr(error, 'code', None)!r}; "
        f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]}"
    )


@calls
def test_refused_dataset_call_with_environment_value_other_than_one_reports_the_refusal_code(net, monkeypatch, call):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "true")

    _, error = _attempt(lambda: CALLS[call](f"http://api.futureagi.com:{net.target.port}"))

    counts = _counts(net)
    assert counts == (0, 0, 0, 0), f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]}"
    assert isinstance(error, DatasetError), repr(error)
    assert error.get_error_code() == CODE, (
        f"get_error_code()={error.get_error_code()!r}, .code={getattr(error, 'code', None)!r}; "
        f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]}"
    )


# ---------------------------------------------------------------------------------------------
# controls: a DatasetError raised for another reason keeps its own code
# ---------------------------------------------------------------------------------------------


def test_dataset_error_built_directly_reports_the_dataset_code():
    error = DatasetError("some dataset failure")

    assert getattr(error, "code", None) is None
    assert error.get_error_code() == DATASET_CODE


def test_dataset_not_found_error_reports_its_own_code():
    assert DatasetNotFoundError("missing").get_error_code() == "DATASET_NOT_FOUND"


@pytest.mark.parametrize("call", ["get-dataset-config", "dataset-by-name"])
def test_unreadable_answer_from_a_loopback_listener_reports_the_dataset_code(net, monkeypatch, call):
    use_proxy(monkeypatch, net)

    _, error = _attempt(lambda: CALLS[call](f"http://127.0.0.1:{net.target.port}"))

    counts = _counts(net)
    assert counts[0] == 1 and counts[1] > 0 and counts[2:] == (0, 0), (
        f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]}"
    )
    assert isinstance(error, DatasetError), repr(error)
    assert getattr(error, "code", None) is None, f"{type(error).__name__}: {error}"
    assert error.get_error_code() == DATASET_CODE, f"get_error_code()={error.get_error_code()!r}"


def test_connection_failure_to_a_loopback_port_reports_the_dataset_code(net, monkeypatch):
    use_proxy(monkeypatch, net)
    closed = socket.socket()
    closed.bind(("127.0.0.1", 0))
    port = closed.getsockname()[1]
    closed.close()

    _, error = _attempt(lambda: CALLS["get-dataset-config"](f"http://127.0.0.1:{port}"))

    counts = _counts(net)
    assert counts == (0, 0, 0, 0), f"target {counts[0]}/{counts[1]}, proxy {counts[2]}/{counts[3]}"
    assert isinstance(error, DatasetError), repr(error)
    assert getattr(error, "code", None) is None, f"{type(error).__name__}: {error}"
    assert error.get_error_code() == DATASET_CODE, f"get_error_code()={error.get_error_code()!r}"
