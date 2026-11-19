"""The platform origin. Derivation; same-source acceptance; refusal on
mixed sources without the flag; mixed credentials refused; Bearer mode; selectors; and that a bad
platform setting never breaks a core namespace."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import fi.errors as errors
from fi._core import origins
from fi._credentials import resolve as resolve_credentials

KEYS = {"api_key": "k-test-1234", "secret_key": "s-test-1234"}


def _resolve(environ=None, login=None, tmp_path=None, allow=None, **kw):
    login_file = None
    if login is not None:
        login_file = tmp_path / "login.json"
        login_file.write_text(json.dumps(login))
    creds = resolve_credentials(
        kw.pop("api_key", None),
        kw.pop("secret_key", None),
        kw.pop("base_url", None),
        environ=environ or {},
        login_file=login_file or (tmp_path / "none.json"),
        **kw,
    )
    return creds, origins.resolve_platform(creds, allow_custom_platform_url=allow, environ=environ or {})


def test_the_origin_derives_from_the_base_url(tmp_path):
    creds, o = _resolve(tmp_path=tmp_path, base_url="https://fa.example.org", **KEYS)
    assert o.base == "https://fa.example.org/omega/api" and o.source == "derived"
    # derived is always exempt: the keys already go to that host for the core namespaces
    creds, o = _resolve(tmp_path=tmp_path, environ={"FI_BASE_URL": "http://fa.internal:8000"}, **KEYS)
    assert o.base == "http://fa.internal:8000/omega/api" and o.source == "derived"
    creds, o = _resolve(tmp_path=tmp_path, **KEYS)
    assert o.base == "https://api.futureagi.com/omega/api"


def test_same_explicit_source_is_accepted_anywhere(tmp_path):
    _, o = _resolve(tmp_path=tmp_path, platform_base_url="https://ee.example.org/omega/api", **KEYS)  # both arguments
    assert o.source == "argument" and o.mode == "keys" and not o.custom
    env = {
        "FI_API_KEY": "k-env-1234",
        "FI_SECRET_KEY": "s-env-1234",
        "FI_PLATFORM_BASE_URL": "http://ee.lan:8080/omega/api",
    }
    _, o = _resolve(tmp_path=tmp_path, environ=env)  # both environment
    assert o.source == "env" and o.headers["X-Api-Key"] == "k-env-1234"
    login = {
        "base_url": "https://fa.example.org",
        "api_key": "k-login-1",
        "secret_key": "s-login-1",
        "platform_base_url": "https://ee.example.org/api",
    }
    _, o = _resolve(tmp_path=tmp_path, login=login)  # both the saved login
    assert o.source == "login" and o.base == "https://ee.example.org/api"


def test_the_zone_and_loopback_are_accepted_from_any_source(tmp_path):
    env = {"FI_PLATFORM_BASE_URL": "https://staging.futureagi.com/omega/api"}
    assert _resolve(tmp_path=tmp_path, environ=env, **KEYS)[1].base == "https://staging.futureagi.com/omega/api"
    env = {"FI_PLATFORM_BASE_URL": "http://127.0.0.1:18700/omega/api"}
    assert _resolve(tmp_path=tmp_path, environ=env, **KEYS)[1].base.startswith("http://127.0.0.1:18700")


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/omega/api",
        "https://futureagi.com.evil.example/omega/api",
        "https://xn--futureag-xxx.com/omega/api",
        "http://staging.futureagi.com/omega/api",  # the zone, but plain http
    ],
)
def test_mixed_sources_are_refused_without_the_flag(tmp_path, url):
    with pytest.raises(errors.HostNotAllowedError) as info:
        _resolve(tmp_path=tmp_path, environ={"FI_PLATFORM_BASE_URL": url}, **KEYS)  # keys: arguments; origin: env
    assert "allow_custom_platform_url" in str(info.value) and "k-test-1234" not in str(info.value)
    assert isinstance(info.value, errors.ConfigurationError)


def test_a_saved_login_never_sends_its_keys_to_an_origin_from_the_environment(tmp_path):
    login = {"base_url": "https://api.futureagi.com", "api_key": "k-login-1", "secret_key": "s-login-1"}
    with pytest.raises(errors.HostNotAllowedError):
        _resolve(
            tmp_path=tmp_path, login=login, environ={"FI_PLATFORM_BASE_URL": "https://cloned-repo.example/omega/api"}
        )


def test_the_flag_allows_it_with_one_stderr_warning(tmp_path, capsys):
    origins._warned.clear()
    env = {"FI_PLATFORM_BASE_URL": "https://ee.corp.example/omega/api"}
    _, o = _resolve(tmp_path=tmp_path, environ=env, allow=True, **KEYS)
    _resolve(tmp_path=tmp_path, environ=env, allow=True, **KEYS)
    assert o.custom
    err = capsys.readouterr().err
    assert err.count("ee.corp.example") == 1 and "k-test-1234" not in err
    _, o = _resolve(tmp_path=tmp_path, environ={**env, "FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}, **KEYS)
    assert o.custom
    with pytest.raises(errors.HostNotAllowedError):  # an explicit False beats the environment
        _resolve(tmp_path=tmp_path, environ={**env, "FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}, allow=False, **KEYS)


def test_mixed_credentials_are_refused(tmp_path):
    with pytest.raises(errors.MixedCredentialsError):
        _resolve(tmp_path=tmp_path, platform_token="ee-token-123456", **KEYS)
    with pytest.raises(errors.MixedCredentialsError):
        env = {"FI_API_KEY": "k-env-1234", "FI_SECRET_KEY": "s-env-1234", "FI_PLATFORM_TOKEN": "ee-token-123456"}
        _resolve(tmp_path=tmp_path, environ=env)


def test_bearer_mode_sends_only_the_token_and_its_selectors(tmp_path):
    env = {
        "FI_PLATFORM_TOKEN": "ee-token-123456",
        "FI_PLATFORM_BASE_URL": "http://ee.lan:8080",
        # This test covers token/selector isolation, not default scheme refusal.
        "FI_ALLOW_INSECURE_HTTP": "1",
        "FI_WORKSPACE_ID": "ws-1",
        "FI_ORGANIZATION_ID": "org-1",
    }
    _, o = _resolve(tmp_path=tmp_path, environ=env)
    assert o.mode == "bearer" and o.headers == {
        "Authorization": "Bearer ee-token-123456",
        "X-Omega-Workspace": "ws-1",
        "X-Omega-Org": "org-1",
    }
    assert "ee-token-123456" not in repr(o)


def test_selectors_are_sent_only_when_set(tmp_path):
    _, o = _resolve(tmp_path=tmp_path, **KEYS)
    assert set(o.headers) == {"X-Api-Key", "X-Secret-Key"}  # unset: the server uses the key's own workspace
    _, o = _resolve(tmp_path=tmp_path, workspace_id="ws-9", organization_id="org-9", **KEYS)
    assert o.headers["X-Workspace-Id"] == "ws-9" and o.headers["X-Organization-Id"] == "org-9"


@pytest.mark.parametrize(
    "url",
    [
        "ftp://ee.example/x",
        "https://user:pw@ee.example/x",
        "https://ee.example/x?a=1",
        "https://ee.example/x#f",
        "not a url",
    ],
)
def test_an_unusable_origin_is_platform_not_configured(tmp_path, url):
    with pytest.raises(errors.PlatformNotConfiguredError) as info:
        _resolve(tmp_path=tmp_path, platform_base_url=url, **KEYS)
    assert "pw" not in str(info.value)


def test_no_keys_and_no_token_is_credentials_missing_with_the_token_hint(tmp_path):
    with pytest.raises(errors.CredentialsMissingError) as info:
        _resolve(tmp_path=tmp_path)
    assert "FI_PLATFORM_TOKEN" in str(info.value) and isinstance(info.value, errors.AuthError)


# Pinned here so the two languages cannot drift (origins.test.ts has the same rows): the key pair comes from one
# place. A half pair from the arguments never borrows the other half from the environment, so the
# guard's "same source as the keys" always names one source for both keys.
@pytest.mark.parametrize(
    "kw, env, missing",
    [
        (  # reverse: secret_key argument, FI_API_KEY and a non-zone origin in the environment
            {"secret_key": "s-arg-reverse", "base_url": "https://api.futureagi.com"},
            {"FI_API_KEY": "k-env-reverse", "FI_PLATFORM_BASE_URL": "https://evil.example/omega/api"},
            "FI_API_KEY",
        ),
        (  # forward: api_key and a non-zone origin as arguments, FI_SECRET_KEY in the environment
            {
                "api_key": "k-arg-forward",
                "base_url": "https://api.futureagi.com",
                "platform_base_url": "https://evil.example/omega/api",
            },
            {"FI_SECRET_KEY": "s-env-forward"},
            "FI_SECRET_KEY",
        ),
        ({"api_key": "k-arg-derived"}, {"FI_SECRET_KEY": "s-env-derived"}, "FI_SECRET_KEY"),  # derived origin
    ],
)
def test_a_split_key_pair_is_credentials_missing_never_sent(tmp_path, kw, env, missing):
    with pytest.raises(errors.CredentialsMissingError) as info:
        _resolve(tmp_path=tmp_path, environ=env, **kw)
    message = str(info.value)
    assert f"No {missing}" in message and "The key pair comes from one place" in message
    for value in [*kw.values(), *env.values()]:
        if value.startswith(("k-", "s-")):
            assert value not in message


def test_a_split_key_pair_is_refused_even_with_the_allow_flag(tmp_path):
    env = {"FI_SECRET_KEY": "s-env-flag", "FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}
    with pytest.raises(errors.CredentialsMissingError):
        _resolve(
            tmp_path=tmp_path,
            environ=env,
            allow=True,
            api_key="k-arg-flag",
            platform_base_url="https://ee.corp.example/x",
        )


def test_an_argument_pair_ignores_the_environments_keys(tmp_path):
    _, o = _resolve(tmp_path=tmp_path, environ={"FI_API_KEY": "k-env-other", "FI_SECRET_KEY": "s-env-other"}, **KEYS)
    assert (o.headers["X-Api-Key"], o.headers["X-Secret-Key"]) == ("k-test-1234", "s-test-1234")
    with pytest.raises(errors.CredentialsMissingError) as info:
        _resolve(tmp_path=tmp_path, environ={"FI_API_KEY": "k-env-only"})
    assert "No FI_SECRET_KEY for" in str(info.value) and "one place" not in str(info.value)


# One verdict table for the host guard, read by both languages
# (src/_core/__tests__/origins.test.ts reads the same file), so the two URL parsers cannot drift.
GUARD_TABLE = Path(__file__).parents[3] / "tests" / "fixtures" / "platform-origins" / "guard-urls.json"
GUARD_CASES = json.loads(GUARD_TABLE.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize(
    "url, verdict", [(c["url"], c["verdict"]) for c in GUARD_CASES], ids=[repr(c["url"]) for c in GUARD_CASES]
)
def test_the_shared_guard_table(tmp_path, url, verdict):
    try:
        _resolve(tmp_path=tmp_path, environ={"FI_PLATFORM_BASE_URL": url}, **KEYS)
        got = "allow"
    except errors.HostNotAllowedError:
        got = "refuse:host"
    except errors.PlatformNotConfiguredError as exc:
        assert exc.code == "invalid_platform_url"
        got = "refuse:invalid"
    assert got == verdict
