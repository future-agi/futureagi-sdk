"""Keyed Knowledge Base requests over plain http:// to a host that is not loopback.

Each case calls one ``fi.kb.KnowledgeBase`` method against a loopback listener that a name such as
``api.futureagi.com`` resolves to, and reads what reached the target and proxy listeners. Without the
opt-in the request is refused before a connection is made, and the refusal reaches the caller as it is
(``.code == "insecure_http_origin"``), whatever the method had or had not prepared before the request.
"""

from __future__ import annotations

import pytest

from fi.kb.client import KnowledgeBase
from fi.kb.types import KnowledgeBaseConfig
from fi.utils.errors import SDKException
from tests.test_plain_http_key_guards import CODE, KEY, SECRET, Net, Sink, net, refused, use_proxy  # noqa: F401

KB_ID = "00000000-0000-4000-8000-000000000001"
HOSTS = pytest.mark.parametrize("host", ["api.futureagi.com", "plain.example.test"], ids=["api-host", "plain-host"])
PROXIES = pytest.mark.parametrize(
    "proxy",
    [(), ("HTTP_PROXY",), ("ALL_PROXY",), ("http_proxy", "all_proxy")],
    ids=["no-proxy", "http-proxy", "all-proxy", "lowercase-proxies"],
)


def _kb(base: str, **kwargs) -> KnowledgeBase:
    return KnowledgeBase(fi_api_key=KEY, fi_secret_key=SECRET, fi_base_url=base, **kwargs)


def _attempt(call):
    try:
        call()
    except Exception as exc:  # the listener's reply may fail to parse; the error is what is read
        return exc
    return None


@pytest.fixture
def notes(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("notes")
    return str(path)


# ---------------------------------------------------------------------------------------------
# update_kb that must first look the Knowledge Base up by name
# ---------------------------------------------------------------------------------------------


UPDATE_LOOKUPS = pytest.mark.parametrize(
    "cached, with_files",
    [
        (None, False),
        (None, True),
        ("other", False),
        ("other", True),
    ],
    ids=["nothing-cached", "nothing-cached-with-files", "other-name-cached", "other-name-cached-with-files"],
)


@HOSTS
@PROXIES
@UPDATE_LOOKUPS
def test_update_kb_that_looks_up_the_name_is_refused_with_the_plain_http_code(monkeypatch, net, notes, host, proxy, cached, with_files):
    use_proxy(monkeypatch, net, names=proxy)
    kb = _kb(f"http://{host}:{net.target.port}")
    if cached is not None:
        kb.kb = KnowledgeBaseConfig(id=KB_ID, name=cached)
    exc = _attempt(lambda: kb.update_kb(kb_name="docs", new_name="renamed", file_paths=[notes] if with_files else None))
    net.nothing_sent()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# other Knowledge Base methods against the same hosts (these already refuse)
# ---------------------------------------------------------------------------------------------


def _update_cached_same_name(base, notes):
    kb = _kb(base)
    kb.kb = KnowledgeBaseConfig(id=KB_ID, name="docs")
    kb.update_kb(kb_name="docs", file_paths=[notes])


CALLS = {
    "constructor-with-name": lambda base, notes: _kb(base, kb_name="docs"),
    "update-kb-same-name-cached": _update_cached_same_name,
    "create-kb": lambda base, notes: _kb(base).create_kb(name="docs"),
    "create-kb-with-files": lambda base, notes: _kb(base).create_kb(name="docs", file_paths=[notes]),
    "delete-kb-by-name": lambda base, notes: _kb(base).delete_kb(kb_names="docs"),
    "delete-kb-by-names": lambda base, notes: _kb(base).delete_kb(kb_names=["docs", "more"]),
    "delete-kb-by-id": lambda base, notes: _kb(base).delete_kb(kb_ids=KB_ID),
    "delete-files-by-kb-name": lambda base, notes: _kb(base).delete_files_from_kb(file_names=["notes.txt"], kb_name="docs"),
}


@HOSTS
@PROXIES
@pytest.mark.parametrize("call", list(CALLS), ids=list(CALLS))
def test_other_kb_methods_are_refused_with_the_plain_http_code(monkeypatch, net, notes, host, proxy, call):
    use_proxy(monkeypatch, net, names=proxy)
    exc = _attempt(lambda: CALLS[call](f"http://{host}:{net.target.port}", notes))
    net.nothing_sent()
    refused(exc, ValueError)


# ---------------------------------------------------------------------------------------------
# controls: loopback and the opt-in send the lookup directly, through no proxy
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "host, opt_in",
    [("127.0.0.1", None), ("localhost", None), ("plain.example.test", True)],
    ids=["loopback-address", "loopback-name", "opt-in-argument"],
)
def test_update_kb_lookup_to_loopback_or_with_opt_in_is_sent_directly(monkeypatch, net, host, opt_in):
    use_proxy(monkeypatch, net)
    kwargs = {} if opt_in is None else {"allow_insecure_http": opt_in}
    exc = _attempt(lambda: _kb(f"http://{host}:{net.target.port}", **kwargs).update_kb(kb_name="docs", new_name="renamed"))
    net.delivered_direct()
    # the listener's empty reply names no Knowledge Base
    assert isinstance(exc, SDKException), f"{type(exc).__name__}: {exc}"
    assert getattr(exc, "code", None) != CODE


def test_update_kb_lookup_with_opt_in_environment_is_sent_directly(monkeypatch, net):
    use_proxy(monkeypatch, net)
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    exc = _attempt(lambda: _kb(f"http://plain.example.test:{net.target.port}").update_kb(kb_name="docs", new_name="renamed"))
    net.delivered_direct()
    assert isinstance(exc, SDKException), f"{type(exc).__name__}: {exc}"
    assert getattr(exc, "code", None) != CODE
