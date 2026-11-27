"""``APIKeyManager`` with no keys of its own, after two clients with explicit keys exist in the process.

Each case builds client A and then client B, each with its own marker keys, either as ``APIKeyAuth`` (as the
``fi.prompt`` classmethods build it) or as ``fi.client.Client``. The base URL of both clients is the loopback
target listener of the ``net`` shim from ``test_plain_http_key_guards``. ``FI_API_KEY`` and ``FI_SECRET_KEY`` are
unset unless a case sets them. The ``APIKeyManager`` singleton and the key attributes held on the client classes
are reset to the state of a fresh import for each case and put back afterwards.

Each case counts, at each sink, the bytes holding each tenant's markers: the headers the manager hands out, the
text of any ``MissingAuthError`` raised, and the bytes that reached the target and proxy listeners.
"""

from __future__ import annotations

import secrets
from typing import Dict, List, Optional

import pytest

from fi.api.auth import APIKeyAuth, APIKeyManager
from fi.client import Client
from fi.utils.errors import MissingAuthError
from tests.test_plain_http_key_guards import _marker_forms, net  # noqa: F401

CODE = "MISSING_FI_CLIENT_AUTHENTICATION"
KEY_NAMES = ("_fi_api_key", "_fi_secret_key")
ENV_NAMES = ("FI_API_KEY", "FI_SECRET_KEY")
KINDS = {"api-key-auth": APIKeyAuth, "fi-client": Client}


class Tenant:
    def __init__(self, letter: str) -> None:
        self.letter = letter
        self.key = "fikey-" + letter.lower() + "-" + secrets.token_hex(10)
        self.secret = "fisec-" + letter.lower() + "-" + secrets.token_hex(10)

    def count(self, raw: bytes) -> int:
        return sum(raw.count(form) for form in _marker_forms(self.key, self.secret))


def _headers_bytes(headers: Optional[Dict]) -> bytes:
    if not headers:
        return b""
    return b"".join(f"{name}: {value}\r\n".encode() for name, value in headers.items())


def _report(sinks: Dict[str, bytes], tenants: List[Tenant]) -> str:
    parts = []
    for sink, raw in sinks.items():
        counts = ", ".join(f"{t.letter}={t.count(raw)}" for t in tenants)
        parts.append(f"{sink}: {counts}")
    return "marker bytes per tenant at each sink -> " + "; ".join(parts)


def _fresh_state(monkeypatch) -> None:
    """Class state as a fresh import holds it: no manager instance, no key attributes on ``APIKeyManager`` or
    ``Client``, and on ``APIKeyAuth`` only the class value ``None`` when the class sets one.
    Attributes a case sets on these classes are taken away when the case ends."""
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(APIKeyManager, "_instance", None)
    for cls in (APIKeyManager, Client):
        for name in KEY_NAMES:
            if name in vars(cls):
                monkeypatch.delattr(cls, name, raising=False)
            else:
                # register removal at the end of the case of whatever the case sets here
                monkeypatch.setattr(cls, name, None, raising=False)
                monkeypatch.delattr(cls, name)
    for name in KEY_NAMES:
        if name in vars(APIKeyAuth):
            monkeypatch.setattr(APIKeyAuth, name, None)


def _two_clients(kind: str, net) -> List[Tenant]:  # noqa: F811
    a, b = Tenant("A"), Tenant("B")
    base = f"http://127.0.0.1:{net.target.port}"
    made = []
    for tenant in (a, b):
        made.append(KINDS[kind](fi_api_key=tenant.key, fi_secret_key=tenant.secret, fi_base_url=base))
    for client in made:
        client.close()
    return [a, b]


def _read_headers(manager):
    """``(headers, error)`` from reading ``manager.headers``."""
    try:
        return manager.headers, None
    except MissingAuthError as exc:
        return None, exc


def _sinks(net, headers=None, error: Optional[BaseException] = None) -> Dict[str, bytes]:  # noqa: F811
    return {
        "headers": _headers_bytes(headers),
        "error text": str(error).encode() if error is not None else b"",
        "target listener": net.target.raw,
        "proxy listener": net.proxy.raw,
    }


def _hands_out_no_keys(manager, net, tenants: List[Tenant]) -> None:  # noqa: F811
    headers, error = _read_headers(manager)
    sinks = _sinks(net, headers, error)
    report = _report(sinks, tenants)
    for tenant in tenants:
        for sink, raw in sinks.items():
            assert tenant.count(raw) == 0, f"{tenant.letter}'s keys at {sink}; headers={headers!r}; {report}"
    if error is not None:
        assert error.get_error_code() == CODE, report
    else:
        assert not (headers.get("X-Api-Key") or headers.get("X-Secret-Key")), f"headers={headers!r}; {report}"


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_manager_without_env_keys_raises_missing_auth(kind, monkeypatch, net):  # noqa: F811
    _fresh_state(monkeypatch)
    tenants = _two_clients(kind, net)
    with pytest.raises(MissingAuthError) as info:
        APIKeyManager()
    report = _report(_sinks(net, error=info.value), tenants)
    assert info.value.get_error_code() == CODE, report
    for tenant in tenants:
        assert tenant.count(str(info.value).encode()) == 0, report


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_singleton_held_after_refusal_hands_out_no_client_keys(kind, monkeypatch, net):  # noqa: F811
    _fresh_state(monkeypatch)
    tenants = _two_clients(kind, net)
    with pytest.raises(MissingAuthError):
        APIKeyManager()
    held = APIKeyManager._instance
    assert isinstance(held, APIKeyManager), f"held instance: {held!r}"
    _hands_out_no_keys(held, net, tenants)


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_singleton_from_new_on_fresh_state_hands_out_no_client_keys(kind, monkeypatch, net):  # noqa: F811
    _fresh_state(monkeypatch)
    tenants = _two_clients(kind, net)
    manager = APIKeyManager.__new__(APIKeyManager)
    assert APIKeyManager._instance is manager
    _hands_out_no_keys(manager, net, tenants)


@pytest.mark.parametrize("kind", sorted(KINDS))
def test_manager_reads_env_keys_then_refuses_without_env(kind, monkeypatch, net):  # noqa: F811
    _fresh_state(monkeypatch)
    a, b = _two_clients(kind, net)
    e = Tenant("E")
    tenants = [a, b, e]
    monkeypatch.setenv("FI_API_KEY", e.key)
    monkeypatch.setenv("FI_SECRET_KEY", e.secret)

    headers = APIKeyManager().headers
    sinks = _sinks(net, headers)
    report = _report(sinks, tenants)
    assert headers == {"X-Api-Key": e.key, "X-Secret-Key": e.secret}, f"headers={headers!r}; {report}"
    assert (a.count(sinks["headers"]), b.count(sinks["headers"])) == (0, 0), report

    for name in ENV_NAMES:
        monkeypatch.delenv(name)
    with pytest.raises(MissingAuthError) as info:
        APIKeyManager()
    assert info.value.get_error_code() == CODE, _report(_sinks(net, error=info.value), tenants)
    _hands_out_no_keys(APIKeyManager._instance, net, tenants)
