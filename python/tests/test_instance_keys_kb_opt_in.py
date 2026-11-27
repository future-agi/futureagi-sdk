"""KB uploads (``fi.kb``) from a client with the plain-http opt-in, and from a client built beside a failed one.

Two tenants, A and B, each hold their own marker keys, generated per case. Client A is a ``KnowledgeBase``
created first. Client B is a second ``KnowledgeBase``, created afterwards with B's keys:

* in the opt-in cases, A has ``allow_insecure_http=True`` and talks to ``http://api.futureagi.com:<port>``,
  a name the ``net`` lookup shim of ``test_plain_http_key_guards`` resolves to A's listener on 127.0.0.1;
  B has no opt-in (the default base or an https base) and sends nothing;
* in the failed-constructor cases, B is given only one of its two keys and raises ``MissingAuthError``.

Then A uploads a file through ``create_kb`` and through ``update_kb``. Every case counts, at each listener
(A's site, and the ``net`` target and proxy listeners, with the proxy variables pointing at the ``net``
proxy), the connections and the bytes holding each tenant's markers, and every assertion message prints
those counts. A's site holds A's markers and none of B's; the ``net`` listeners hold none of either.
"""

from __future__ import annotations

import contextlib
import secrets
import threading
import time
from typing import Dict, Iterator, Optional, Tuple

import pytest

from fi.api.auth import APIKeyAuth
from fi.kb.client import KnowledgeBase
from fi.utils.errors import MissingAuthError
from tests.test_keyed_request_paths import Site
from tests.test_plain_http_key_guards import _marker_forms, net, use_proxy  # noqa: F401

KB_ID = "00000000-0000-4000-8000-0000000000b2"
KB_PATH = "/model-hub/knowledge-base/"
SHIM_HOST = "api.futureagi.com"
KEY_ATTRIBUTES = ("_fi_api_key", "_fi_secret_key")
CLASSES = (APIKeyAuth, KnowledgeBase)
_MISSING = object()


class _Tenant:
    """A tenant's marker keys, distinct for every tenant and every case."""

    def __init__(self, letter: str) -> None:
        self.letter = letter
        self.key = f"fikey-{letter.lower()}-" + secrets.token_hex(10)
        self.secret = f"fisec-{letter.lower()}-" + secrets.token_hex(10)

    def count(self, raw: bytes) -> int:
        """The number of bytes in ``raw`` that hold this tenant's markers, raw or base64."""
        return sum(raw.count(form) * len(form) for form in _marker_forms(self.key, self.secret))


def _route(method: str, path: str) -> Tuple[int, Dict[str, str], bytes]:
    if path == KB_PATH and method != "GET":
        body = b'{"status": true, "result": {"kb_id": "%s", "kb_name": "docs", "id": "%s", "name": "docs", "file_ids": []}}' % (
            KB_ID.encode(),
            KB_ID.encode(),
        )
        return 200, {"Content-Type": "application/json"}, body
    return 200, {"Content-Type": "application/json"}, b"{}"


def _snapshot(listener) -> Tuple[int, bytes]:
    lock = getattr(listener, "_lock", None) or threading.Lock()
    with lock:
        return listener.connections, bytes(listener.raw)


class _Scene:
    """The two tenants, the listeners and the connection and per-tenant marker byte counts at each listener."""

    def __init__(self, net, site_a: Site) -> None:
        self.a, self.b = _Tenant("A"), _Tenant("B")
        self.listeners = {"site-a": site_a, "net-target": net.target, "net-proxy": net.proxy}

    def counts(self) -> Dict[str, Dict[str, int]]:
        time.sleep(0.15)
        counts = {}
        for name, listener in self.listeners.items():
            connections, raw = _snapshot(listener)
            counts[name] = {"connections": connections, "A": self.a.count(raw), "B": self.b.count(raw)}
        return counts

    @staticmethod
    def report(counts: Dict[str, Dict[str, int]]) -> str:
        return "connections and per-tenant marker bytes: " + "; ".join(
            f"{name}: {value['connections']} connections, A={value['A']} B={value['B']}" for name, value in counts.items()
        )

    def check(self, label: str, error: Optional[BaseException]) -> None:
        """A's upload completed; A's site holds A's markers only; the ``net`` listeners hold no markers."""
        counts = self.counts()
        message = f"{label}: {self.report(counts)}; error: {error!r}"
        assert error is None, message
        assert counts["site-a"]["A"] > 0, message
        assert counts["site-a"]["B"] == 0, message
        for name in ("net-target", "net-proxy"):
            assert (counts[name]["connections"], counts[name]["A"], counts[name]["B"]) == (0, 0, 0), message


@contextlib.contextmanager
def _scene(net, monkeypatch) -> Iterator[_Scene]:
    """A's listener and two tenants, with FI_API_KEY and FI_SECRET_KEY unset and the proxy variables pointing
    at the ``net`` proxy. The key attributes the client classes hold on the class itself, if any, are put back
    as they were when the case ends."""
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)
    use_proxy(monkeypatch, net, names=("HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"))
    saved = {(cls, name): cls.__dict__.get(name, _MISSING) for cls in CLASSES for name in KEY_ATTRIBUTES}
    site_a = Site(_route)
    try:
        yield _Scene(net, site_a)
    finally:
        site_a.close()
        for (cls, name), value in saved.items():
            if value is _MISSING:
                if name in cls.__dict__:
                    delattr(cls, name)
            else:
                setattr(cls, name, value)


def _notes(tmp_path, letter: str) -> str:
    path = tmp_path / f"notes-{letter.lower()}.txt"
    path.write_text(f"notes for tenant {letter}")
    return str(path)


def _attempt(call) -> Optional[BaseException]:
    try:
        call()
    except Exception as exc:  # the error is read with the listener counts
        return exc
    return None


def _uploads_from_a(s: _Scene, kb_a: KnowledgeBase, path: str) -> None:
    """A uploads ``path`` through ``create_kb``, then through ``update_kb`` on the Knowledge Base it created."""
    error = _attempt(lambda: kb_a.create_kb(name="docs", file_paths=[path]))
    s.check("after A's create_kb upload", error)
    assert kb_a.kb is not None and str(kb_a.kb.id) == KB_ID, repr(kb_a.kb)

    error = _attempt(lambda: kb_a.update_kb(kb_name="docs", file_paths=[path]))
    s.check("after A's create_kb and update_kb uploads", error)
    requests_a = s.listeners["site-a"].requests
    assert [path for _, path in requests_a] == [KB_PATH, KB_PATH] and requests_a[0][0] == "POST", requests_a


# ---------------------------------------------------------------------------------------------
# A has the plain-http opt-in; B, built afterwards, has none
# ---------------------------------------------------------------------------------------------


def _kb_b_without_opt_in(s: _Scene, monkeypatch, b_base: str, b_keys: str) -> KnowledgeBase:
    kwargs = {} if b_base == "default" else {"fi_base_url": f"https://{SHIM_HOST}"}
    if b_keys == "arguments":
        return KnowledgeBase(fi_api_key=s.b.key, fi_secret_key=s.b.secret, **kwargs)
    monkeypatch.setenv("FI_API_KEY", s.b.key)
    monkeypatch.setenv("FI_SECRET_KEY", s.b.secret)
    try:
        return KnowledgeBase(**kwargs)
    finally:
        monkeypatch.delenv("FI_API_KEY", raising=False)
        monkeypatch.delenv("FI_SECRET_KEY", raising=False)


@pytest.mark.parametrize("b_keys", ["arguments", "environment"], ids=["b-keys-as-arguments", "b-keys-from-environment"])
@pytest.mark.parametrize("b_base", ["default", "https"], ids=["b-default-base", "b-https-base"])
def test_kb_uploads_from_opted_in_a_send_a_keys_when_kb_client_b_without_opt_in_exists(net, monkeypatch, tmp_path, b_base, b_keys):
    with _scene(net, monkeypatch) as s:
        site_a = s.listeners["site-a"]
        kb_a = KnowledgeBase(
            fi_api_key=s.a.key,
            fi_secret_key=s.a.secret,
            fi_base_url=f"http://{SHIM_HOST}:{site_a.port}",
            allow_insecure_http=True,
        )
        kb_b = _kb_b_without_opt_in(s, monkeypatch, b_base, b_keys)
        assert kb_b is not kb_a

        _uploads_from_a(s, kb_a, _notes(tmp_path, "A"))


# ---------------------------------------------------------------------------------------------
# B's constructor raises MissingAuthError
# ---------------------------------------------------------------------------------------------


A_BASES = pytest.mark.parametrize("a_base", ["loopback", "opt-in"], ids=["a-loopback-base", "a-opt-in-base"])


def _kb_a(s: _Scene, a_base: str) -> KnowledgeBase:
    site_a = s.listeners["site-a"]
    if a_base == "loopback":
        return KnowledgeBase(fi_api_key=s.a.key, fi_secret_key=s.a.secret, fi_base_url=site_a.base)
    return KnowledgeBase(
        fi_api_key=s.a.key,
        fi_secret_key=s.a.secret,
        fi_base_url=f"http://{SHIM_HOST}:{site_a.port}",
        allow_insecure_http=True,
    )


@A_BASES
@pytest.mark.parametrize("given", ["api-key-only", "secret-key-only"], ids=["b-api-key-only", "b-secret-key-only"])
def test_kb_uploads_from_a_send_a_keys_when_kb_client_b_with_one_key_raises(net, monkeypatch, tmp_path, a_base, given):
    with _scene(net, monkeypatch) as s:
        kb_a = _kb_a(s, a_base)

        if given == "api-key-only":
            with pytest.raises(MissingAuthError) as raised:
                KnowledgeBase(fi_api_key=s.b.key)
            assert (raised.value.missing_api_key, raised.value.missing_secret_key) == (False, True)
        else:
            with pytest.raises(MissingAuthError) as raised:
                KnowledgeBase(fi_secret_key=s.b.secret)
            assert (raised.value.missing_api_key, raised.value.missing_secret_key) == (True, False)
        assert s.b.key not in str(raised.value) and s.b.secret not in str(raised.value)

        _uploads_from_a(s, kb_a, _notes(tmp_path, "A"))
