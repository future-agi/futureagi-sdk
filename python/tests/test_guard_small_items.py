"""Plain http refusals: their wording, and the code they keep when a module wraps them in its own exception.

Every case targets a loopback listener through the lookup shim of ``test_plain_http_key_guards``
(``api.futureagi.com`` resolves to the loopback interface) and reads what reached it, so no case reaches a real host.
"""

from __future__ import annotations

import json
import secrets
import socket
import uuid

import pytest

from fi.datasets.dataset import Dataset, LRUCache
from fi.datasets.types import DatasetConfig, ModelTypes
from fi.gateway._utils import check_valid_key
from fi.prompt import Prompt
from fi.prompt.cache import PromptCache
from fi.utils.errors import DatasetError
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, Sink, net, use_proxy  # noqa: F401


def _attempt(call):
    try:
        return call(), None
    except Exception as exc:  # the refusal is what is read
        return None, exc


# ---------------------------------------------------------------------------------------------
# wording
# ---------------------------------------------------------------------------------------------


def test_refusal_names_the_environment_variable_and_the_argument_only_where_accepted(net):
    _, error = _attempt(lambda: check_valid_key(KEY, f"http://api.futureagi.com:{net.target.port}"))

    net.nothing_sent()
    assert getattr(error, "code", None) == CODE, repr(error)
    message = str(error)
    assert "FI_ALLOW_INSECURE_HTTP=1" in message, message
    assert "(or pass allow_insecure_http=True where the client accepts it)" in message, message


# ---------------------------------------------------------------------------------------------
# fi.datasets wraps a refusal in DatasetError, which keeps the refusal code and has it as its context
# ---------------------------------------------------------------------------------------------


@pytest.fixture
def empty_dataset_cache(monkeypatch):
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", LRUCache(capacity=100))


def _dataset_by_name(base: str, **opt):
    config = DatasetConfig(name="refusal-probe", model_type=ModelTypes.GENERATIVE_LLM)
    return Dataset(dataset_config=config, fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, **opt)


def _config_by_name(base: str, **opt):
    return Dataset.get_dataset_config("refusal-probe", fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, **opt)


DATASET_CALLS = {"dataset-by-name": _dataset_by_name, "get-dataset-config": _config_by_name}


@pytest.mark.parametrize("call", list(DATASET_CALLS), ids=list(DATASET_CALLS))
@pytest.mark.parametrize(
    "opt", [{}, {"allow_insecure_http": None}, {"allow_insecure_http": False}], ids=["absent", "none", "false"]
)
def test_dataset_call_without_opt_in_raises_dataset_error_with_the_refusal_code(net, empty_dataset_cache, call, opt):
    _, error = _attempt(lambda: DATASET_CALLS[call](f"http://api.futureagi.com:{net.target.port}", **opt))

    net.nothing_sent()
    assert isinstance(error, DatasetError), repr(error)
    assert getattr(error, "code", None) == CODE, repr(error)
    context = error.__context__
    while context is not None and isinstance(context, DatasetError):
        context = context.__context__
    assert isinstance(context, ValueError) and getattr(context, "code", None) == CODE, repr(context)


# ---------------------------------------------------------------------------------------------
# the prompt template cache serves a template only to a call with the same keys, base URL and opt-in
# ---------------------------------------------------------------------------------------------

KEY_B = "fikey-tenant-b-" + secrets.token_hex(6)
SECRET_B = "fisec-tenant-b-" + secrets.token_hex(6)
TEMPLATE = "cache-probe"


class TemplateSink(Sink):
    """A loopback listener that answers every request with one prompt template. The template id depends on the
    keys the request carries (``ids``), else it is ``default_id``, so a caller can tell whose template it got."""

    def __init__(self, ids: dict | None = None) -> None:
        self.ids = ids or {}
        self.default_id = uuid.uuid4()
        self.requests: list = []
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
            head = data.partition(b"\r\n\r\n")[0]
            fields = {}
            for line in head.split(b"\r\n")[1:]:
                name, _, value = line.partition(b":")
                fields[name.strip().lower().decode("latin-1")] = value.strip().decode("latin-1")
            keys = (fields.get("x-api-key"), fields.get("x-secret-key"))
            with self._lock:
                self.raw += data
                self.requests.append(keys)
            template_id = self.ids.get(keys, self.default_id)
            payload = json.dumps(
                {"result": {"id": str(template_id), "name": TEMPLATE, "version": "v1", "prompt_config": [{}]}}
            ).encode()
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
        from tests.test_plain_http_key_guards import _marker_forms

        with self._lock:
            raw = self.raw
        return sum(raw.count(form) for form in _marker_forms(*values))


@pytest.fixture
def own_prompt_cache(monkeypatch):
    cache = PromptCache(max_workers=0)
    monkeypatch.setattr("fi.prompt.client.prompt_cache", cache)
    return cache


LOOKUPS = {"version": {"version": "v1"}, "label": {"label": "staging"}, "default": {}}
lookups = pytest.mark.parametrize("lookup", list(LOOKUPS), ids=list(LOOKUPS))


def _template(base: str, api_key: str = KEY, secret_key: str = SECRET, lookup: str = "version", **opt):
    return Prompt.get_template_by_name(
        TEMPLATE, fi_api_key=api_key, fi_secret_key=secret_key, fi_base_url=base, **LOOKUPS[lookup], **opt
    )


def _sink_base(host: str, sink: Sink) -> str:
    return f"http://{host}:{sink.port}"


@lookups
@pytest.mark.parametrize(
    "pair", [(KEY_B, SECRET_B), (KEY_B, SECRET), (KEY, SECRET_B)], ids=["both-keys", "api-key", "secret-key"]
)
def test_template_call_with_other_keys_sends_its_own_request(net, own_prompt_cache, lookup, pair):
    api_b, secret_b = pair
    id_a, id_b = uuid.uuid4(), uuid.uuid4()
    sink = TemplateSink(ids={(KEY, SECRET): id_a, (api_b, secret_b): id_b})
    try:
        base = _sink_base("api.futureagi.com", sink)
        a = _template(base, lookup=lookup, allow_insecure_http=True)
        assert a.template.id == id_a
        before = len(sink.requests)

        b = _template(base, api_b, secret_b, lookup=lookup, allow_insecure_http=True)

        assert sink.requests[before:] == [(api_b, secret_b)], sink.requests
        assert b.template.id == id_b
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0)
    finally:
        sink.close()


@lookups
def test_template_call_with_other_base_url_sends_to_its_own_base_url(net, own_prompt_cache, lookup):
    first, second = TemplateSink(), TemplateSink()
    try:
        a = _template(_sink_base("api.futureagi.com", first), lookup=lookup, allow_insecure_http=True)
        assert a.template.id == first.default_id
        first_before = len(first.requests)

        b = _template(_sink_base("plain.example.test", second), lookup=lookup, allow_insecure_http=True)

        assert len(first.requests) == first_before, first.requests
        assert second.requests == [(KEY, SECRET)], second.requests
        assert b.template.id == second.default_id
    finally:
        first.close()
        second.close()


@lookups
@pytest.mark.parametrize(
    "opt, environment",
    [({}, None), ({"allow_insecure_http": None}, None), ({"allow_insecure_http": False}, None),
     ({"allow_insecure_http": False}, "1")],
    ids=["absent", "none", "false", "false-over-environment"],
)
def test_template_call_without_opt_in_after_opted_in_call_is_refused(
    net, monkeypatch, own_prompt_cache, lookup, opt, environment
):
    use_proxy(monkeypatch, net)
    sink = TemplateSink()
    try:
        base = _sink_base("api.futureagi.com", sink)
        _template(base, lookup=lookup, allow_insecure_http=True)
        before = (sink.connections, sink.key_bytes(KEY, SECRET))
        assert before[0] >= 1 and before[1] > 0
        if environment is not None:
            monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", environment)

        _, error = _attempt(lambda: _template(base, lookup=lookup, **opt))

        assert getattr(error, "code", None) == CODE, repr(error)
        assert (sink.connections, sink.key_bytes(KEY, SECRET)) == before
        assert (net.proxy.connections, net.proxy.marker_bytes()) == (0, 0)
    finally:
        sink.close()


@lookups
def test_repeated_template_call_with_same_settings_is_served_from_the_cache(net, own_prompt_cache, lookup):
    sink = TemplateSink()
    try:
        base = _sink_base("api.futureagi.com", sink)
        a = _template(base, lookup=lookup, allow_insecure_http=True)
        before = sink.connections

        b = _template(base, lookup=lookup, allow_insecure_http=True)

        assert sink.connections == before
        assert b.template.id == a.template.id
    finally:
        sink.close()


def test_template_cache_keys_hold_no_raw_key(net, own_prompt_cache):
    sink = TemplateSink()
    try:
        _template(_sink_base("api.futureagi.com", sink), allow_insecure_http=True)
    finally:
        sink.close()
    stored = list(own_prompt_cache._store)
    assert len(stored) == 1, stored
    assert not any(value in key for key in stored for value in (KEY, SECRET)), stored


def test_make_key_without_scope_is_unchanged():
    assert PromptCache.make_key("name") == "name"
    assert PromptCache.make_key("name", version="v1") == "name|v:v1"
    assert PromptCache.make_key("name", label="production") == "name|label:production"
