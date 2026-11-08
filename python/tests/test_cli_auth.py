"""futureagi-py login / logout and doctor's "who you are" (shared CLI core). No network: the
platform client's transport is an httpx.MockTransport; user-info's shape is read from backend
accounts/views/user.py get_user_info (UserSerializer data), not recorded."""

import io
import json
import os
import stat
import sys

import httpx
import pytest

from fi._cli import auth
from fi._cli import main as main_mod

USER = {"email": "e2e@example.test", "name": "E2E", "organization": {"name": "E2E Org"}}


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL", "FI_PLATFORM_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "cfg" / "login.json"))
    yield


def _server(monkeypatch, status=200, body=USER, seen=None):
    def handler(request):
        if seen is not None:
            seen.append((request.url.host, request.url.path, request.headers.get("x-api-key")))
        return httpx.Response(status, json=body)

    real = auth._client

    def client(base_url, api_key, secret_key):
        c = real(base_url, api_key, secret_key)
        c.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
        return c

    monkeypatch.setattr(auth, "_client", client)


def _login(monkeypatch, capsys, *argv, stdin_text="ak-1234567890\nsk-1234567890\n"):
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    code = main_mod.main(["login", *argv])
    return code, capsys.readouterr()


def test_login_verifies_then_saves_0600(monkeypatch, capsys, tmp_path):
    seen = []
    _server(monkeypatch, seen=seen)
    code, out = _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:18000/")
    assert code == 0 and "as e2e@example.test · org E2E Org" in out.out
    assert seen == [("127.0.0.1", "/accounts/user-info/", "ak-1234567890")]
    path = tmp_path / "cfg" / "login.json"
    data = json.loads(path.read_text())
    assert data["base_url"] == "http://127.0.0.1:18000" and data["api_key"] == "ak-1234567890"
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert "ak-1234567890" not in out.out + out.err


def test_refused_keys_are_not_saved(monkeypatch, capsys, tmp_path):
    _server(monkeypatch, status=401, body={"detail": "bad key"})
    code, out = _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:18000")
    assert code == 3 and "refused these keys (HTTP 401); nothing was saved" in out.err
    assert not (tmp_path / "cfg" / "login.json").exists()


def test_from_env_and_no_verify(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("FI_API_KEY", "ak-env-123456")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-env-123456")
    code, out = _login(monkeypatch, capsys, "--from-env", "--no-verify", "--base-url", "http://127.0.0.1:9")
    assert code == 0 and "not checked (--no-verify)" in out.out
    assert json.loads((tmp_path / "cfg" / "login.json").read_text())["secret_key"] == "sk-env-123456"


def test_piped_stdin_needs_two_lines(monkeypatch, capsys):
    code, out = _login(monkeypatch, capsys, "--no-verify", stdin_text="only-one\n")
    assert code == 3 and "two lines" in out.err


def test_saved_login_is_used_then_logout_removes_it(monkeypatch, capsys, tmp_path):
    from fi._credentials import resolve

    _server(monkeypatch)
    _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:18000")
    creds = resolve()
    assert creds.keys_source == "login" and creds.base_url == "http://127.0.0.1:18000"
    assert main_mod.main(["logout"]) == 0
    assert "Removed" in capsys.readouterr().out
    assert not resolve().complete
    assert main_mod.main(["logout"]) == 0 and "No saved login" in capsys.readouterr().out


def test_doctor_says_who_after_where(monkeypatch, capsys):
    _server(monkeypatch)
    monkeypatch.setenv("FI_API_KEY", "ak-env-123456")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-env-123456")
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:18000")
    assert main_mod.main(["doctor"]) == 0
    out = capsys.readouterr().out
    assert out.index("Server") < out.index("Who        e2e@example.test")
    assert main_mod.main(["doctor", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["who"]["user"]["email"] == "e2e@example.test" and "ak-env" not in json.dumps(data)


def test_doctor_offline_and_without_keys(monkeypatch, capsys):
    assert main_mod.main(["doctor"]) == 0
    assert "Who        not checked (no keys)" in capsys.readouterr().out
    monkeypatch.setenv("FI_API_KEY", "ak-env-123456")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-env-123456")
    assert main_mod.main(["doctor", "--offline"]) == 0
    assert "not checked (--offline)" in capsys.readouterr().out


def test_missing_keys_message_names_login_which_exists():
    from fi._credentials import CredentialsMissingError

    msg = str(CredentialsMissingError("http://x", ("FI_API_KEY",)))
    assert "futureagi-py login" in msg
    parser = main_mod.build_parser()
    sub = next(a for a in parser._actions if getattr(a, "choices", None) and "doctor" in a.choices)
    assert {"login", "logout"} <= set(sub.choices)


# ---- the server comes from --base-url, else FI_BASE_URL, else the default ----------------------


def test_login_uses_fi_base_url_and_says_so(monkeypatch, capsys, tmp_path):
    seen = []
    _server(monkeypatch, seen=seen)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:18000/")
    code, out = _login(monkeypatch, capsys)
    assert code == 0, out.err
    assert "Server   http://127.0.0.1:18000  (from FI_BASE_URL)" in out.out
    assert out.out.index("Server") < out.out.index("Logged in")
    assert seen == [("127.0.0.1", "/accounts/user-info/", "ak-1234567890")]  # never the default host
    assert json.loads((tmp_path / "cfg" / "login.json").read_text())["base_url"] == "http://127.0.0.1:18000"
    from fi._credentials import resolve

    creds = resolve()  # with FI_BASE_URL still set, the saved login is the one in use
    assert creds.keys_source == "login" and creds.base_url == "http://127.0.0.1:18000"


def test_login_from_env_takes_fi_base_url_too(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("FI_API_KEY", "ak-env-123456")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-env-123456")
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:18000")
    code, out = _login(monkeypatch, capsys, "--from-env", "--no-verify")
    assert code == 0 and "(from FI_BASE_URL)" in out.out
    assert json.loads((tmp_path / "cfg" / "login.json").read_text())["base_url"] == "http://127.0.0.1:18000"


def test_login_refuses_two_different_servers(monkeypatch, capsys, tmp_path):
    seen = []
    _server(monkeypatch, seen=seen)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:18000")
    code, out = _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:19000")
    assert code == 3 and "name two different servers" in out.err and "Unset FI_BASE_URL" in out.err
    assert seen == [] and not (tmp_path / "cfg" / "login.json").exists()
    code, out = _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:18000/")  # the same server: fine
    assert code == 0 and "(from --base-url)" in out.out


def test_login_names_the_default_server_and_how_to_change_it(monkeypatch, capsys):
    code, out = _login(monkeypatch, capsys, "--no-verify")
    assert code == 0
    assert "Server   https://api.futureagi.com  (from the default; pass --base-url or set FI_BASE_URL" in out.out


# ---- the real user-info shape, and a 200 that is not a user ---------------------------------------

# backend accounts/serializers/contracts.py UserInfoResponseSerializer (the fields login reads)
SERIALIZER_USER = {
    "id": "6c1f9f8e-0000-4000-8000-000000000001",
    "email": "e2e@example.test",
    "name": "E2E",
    "organization": {"id": "6c1f9f8e-0000-4000-8000-000000000002", "name": "e2e-org", "display_name": "E2E Org"},
    "default_workspace_id": "6c1f9f8e-0000-4000-8000-000000000003",
    "default_workspace_name": "default",
    "default_workspace_display_name": "Support team",
}


def test_who_reads_the_serializer_workspace_and_org(monkeypatch, capsys):
    _server(monkeypatch, body=SERIALIZER_USER)
    code, out = _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:18000")
    assert code == 0 and "as e2e@example.test · org E2E Org · workspace Support team" in out.out
    _server(monkeypatch, body={**SERIALIZER_USER, "default_workspace_display_name": ""})
    assert auth.who("http://127.0.0.1:18000", "ak-1", "sk-1")["workspace"] == "default"


@pytest.mark.parametrize("body", ["<html>ok</html>", ["a"], {"status": True, "result": "ok"}])
def test_a_200_that_is_not_a_user_is_one_line(monkeypatch, capsys, tmp_path, body):
    _server(monkeypatch, body=body)
    code, out = _login(monkeypatch, capsys, "--base-url", "http://127.0.0.1:18000")
    assert code == 3 and "answered without a user" in out.err and "nothing was saved" in out.err
    assert "Traceback" not in out.err and not (tmp_path / "cfg" / "login.json").exists()
    monkeypatch.setenv("FI_API_KEY", "ak-env-123456")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-env-123456")
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:18000")
    assert main_mod.main(["doctor"]) == 0
    assert "Who        http://127.0.0.1:18000/accounts/user-info/ answered without a user" in capsys.readouterr().out


def test_who_lines_is_gone():
    assert not hasattr(auth, "who_lines")  # dead code
