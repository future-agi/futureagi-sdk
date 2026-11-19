"""fi._credentials: the platform origin, its source, the selectors and the token."""

import json
import os
import stat
import sys

import pytest

from fi._credentials import derive_platform_base_url, load_login, resolve, save_login


def test_derived_from_the_base_url_when_nothing_sets_it(tmp_path):
    none = tmp_path / "none.json"
    creds = resolve(environ={}, login_file=none)
    assert creds.platform_base_url == "https://api.futureagi.com/omega/api"
    assert creds.platform_base_url_source == "derived"
    creds = resolve(environ={"FI_BASE_URL": "http://fa.local:8000/"}, login_file=none)
    assert creds.platform_base_url == "http://fa.local:8000/omega/api"
    assert (creds.workspace_id, creds.organization_id, creds.platform_token) == (None, None, None)
    assert creds.workspace_id_source == creds.platform_token_source == "none"
    assert derive_platform_base_url("http://x.test/") == "http://x.test/omega/api"


def test_argument_then_env_then_login(tmp_path):
    login = tmp_path / "login.json"
    save_login("k-login", "s-login", "http://fa.test", platform_base_url="http://plat.test/api/",
               workspace_id="ws-login", path=login)
    env = {"FI_PLATFORM_BASE_URL": "http://env-plat.test", "FI_WORKSPACE_ID": "ws-env",
           "FI_ORGANIZATION_ID": "org-env", "FI_PLATFORM_TOKEN": "tok-env"}
    c = resolve(platform_base_url="http://arg-plat.test", workspace_id="ws-arg", platform_token="tok-arg",
                environ=env, login_file=login)
    assert (c.platform_base_url, c.platform_base_url_source) == ("http://arg-plat.test", "argument")
    assert (c.workspace_id, c.workspace_id_source) == ("ws-arg", "argument")
    assert (c.organization_id, c.organization_id_source) == ("org-env", "env")
    assert (c.platform_token, c.platform_token_source) == ("tok-arg", "argument")
    c = resolve(environ=env, login_file=login)
    assert (c.platform_base_url, c.platform_base_url_source) == ("http://env-plat.test", "env")
    assert (c.platform_token, c.platform_token_source) == ("tok-env", "env")
    c = resolve(environ={}, login_file=login)
    assert (c.base_url, c.keys_source) == ("http://fa.test", "login")
    assert (c.platform_base_url, c.platform_base_url_source) == ("http://plat.test/api", "login")
    assert (c.workspace_id, c.workspace_id_source) == ("ws-login", "login")
    assert c.platform_token is None  # the login never stores a token
    # with the login's own keys, the environment's selectors still win over the login's
    c = resolve(environ={"FI_WORKSPACE_ID": "ws-env"}, login_file=login)
    assert (c.keys_source, c.workspace_id, c.workspace_id_source) == ("login", "ws-env", "env")


def test_a_login_bound_elsewhere_gives_no_platform_values(tmp_path):
    login = tmp_path / "login.json"
    save_login("k", "s", "http://fa.test", platform_base_url="http://plat.test", workspace_id="ws", path=login)
    c = resolve(environ={"FI_BASE_URL": "http://other.test"}, login_file=login)
    assert c.keys_source == "none" and c.login_skipped
    assert (c.platform_base_url, c.platform_base_url_source) == ("http://other.test/omega/api", "derived")
    assert c.workspace_id is None
    # same base URL from the environment: the login is still bound, so its origin applies
    c = resolve(environ={"FI_BASE_URL": "http://FA.test/"}, login_file=login)
    assert (c.platform_base_url_source, c.keys_source) == ("login", "login")


def test_env_or_argument_keys_never_take_the_logins_identity(tmp_path):
    """User A's login plus user B's keys on the same base URL. B's keys must not go
    out with A's workspace selector or A's saved platform origin."""
    login = tmp_path / "login.json"
    save_login("k-A", "s-A", "http://fa.internal:8000", platform_base_url="https://plat-a.test",
               workspace_id="ws-A", organization_id="org-A", path=login)
    env = {"FI_API_KEY": "k-B", "FI_SECRET_KEY": "s-B", "FI_BASE_URL": "http://fa.internal:8000"}
    for c in (resolve(environ=env, login_file=login),
              resolve("k-B", "s-B", "http://fa.internal:8000", environ={}, login_file=login)):
        assert c.keys_source in ("env", "argument") and c.api_key == "k-B"
        assert (c.workspace_id, c.workspace_id_source) == (None, "none")
        assert (c.organization_id, c.organization_id_source) == (None, "none")
        assert (c.platform_base_url, c.platform_base_url_source) == ("http://fa.internal:8000/omega/api", "derived")
    # B's own selectors from the environment still apply
    c = resolve(environ={**env, "FI_WORKSPACE_ID": "ws-B"}, login_file=login)
    assert (c.workspace_id, c.workspace_id_source) == ("ws-B", "env")


def test_a_derived_origin_reads_back_as_derived_not_login(tmp_path):
    """save_login stores the derived origin; reading it back must not turn it into a
    login-sourced origin (the host guard treats the two differently)."""
    login = tmp_path / "login.json"
    save_login("k", "s", "http://fa.internal:8000", path=login)
    assert json.loads(login.read_text())["platform_base_url_derived"] is True
    with_file = resolve(environ={}, login_file=login)
    without = resolve(environ={"FI_BASE_URL": "http://fa.internal:8000"}, login_file=tmp_path / "none.json")
    assert with_file.keys_source == "login"
    assert (with_file.platform_base_url, with_file.platform_base_url_source) == (
        without.platform_base_url, without.platform_base_url_source) == ("http://fa.internal:8000/omega/api", "derived")
    # an explicit --platform-base-url equal to the derived one is the derived one too
    save_login("k", "s", "http://fa.internal:8000", platform_base_url="http://FA.internal:8000/omega/api/", path=login)
    assert resolve(environ={}, login_file=login).platform_base_url_source == "derived"
    # a file without the marker whose value is the derivation (written by hand) reads as derived
    login.write_text(json.dumps({"base_url": "http://fa.internal:8000", "api_key": "k", "secret_key": "s",
                                 "platform_base_url": "http://fa.internal:8000/omega/api"}))
    assert resolve(environ={}, login_file=login).platform_base_url_source == "derived"
    # an explicit, different origin stays a login value, with no marker
    save_login("k", "s", "http://fa.internal:8000", platform_base_url="https://plat.test", path=login)
    assert "platform_base_url_derived" not in json.loads(login.read_text())
    c = resolve(environ={}, login_file=login)
    assert (c.platform_base_url, c.platform_base_url_source) == ("https://plat.test", "login")


def test_save_login_derives_the_origin_and_is_private(tmp_path):
    login = tmp_path / "cfg" / "futureagi" / "login.json"
    path = save_login("k-1", "s-1", "http://fa.test/", path=login)
    data = json.loads(path.read_text())
    assert data == {"base_url": "http://fa.test", "platform_base_url": "http://fa.test/omega/api",
                    "platform_base_url_derived": True, "api_key": "k-1", "secret_key": "s-1"}
    assert load_login(path)["platform_base_url"] == "http://fa.test/omega/api"
    if sys.platform != "win32":
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
        assert stat.S_IMODE(os.stat(path.parent).st_mode) == 0o700
    with pytest.raises(ValueError):
        save_login("", "s", "http://fa.test", path=login)


def test_repr_never_shows_a_secret(tmp_path):
    c = resolve("k-secret-1234", "s-secret-5678", "http://fa.test", platform_token="tok-secret-9",
                environ={}, login_file=tmp_path / "none.json")
    text = repr(c)
    assert "k-secret" not in text and "s-secret" not in text and "tok-secret" not in text
    assert "http://fa.test" in text
