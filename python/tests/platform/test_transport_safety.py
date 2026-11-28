"""Public client checks for HTTP opt-in, credential handling, and redirects."""
import logging
import warnings
from uuid import uuid4

import httpx
import pytest
from fi import errors

from ._transport_test_support import (
    API_KEY,
    EU,
    NOT_APPLICABLE_AT_FOLD,
    SANDBOX_ABSENT,
    SECRET_KEY,
    TOKEN,
    US,
    assert_private,
    assert_selected_only,
    close,
    invoke,
    run,
)


def warning_texts(recorded, capsys, caplog):
    return ([str(w.message) for w in recorded] +
            [line for line in capsys.readouterr().err.splitlines() if line.strip()] +
            [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING])


def assert_warning_safety(texts, expected, *, keys=False):
    assert len(texts) == expected, "one notice per process, not per request/client/path/origin"
    for text in texts:
        assert "FI_ALLOW_INSECURE_HTTP" in text and "http://" in text
        assert API_KEY not in text and SECRET_KEY not in text and TOKEN not in text
        assert "private-path" not in text


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("source", ["argument", "environment", "derived"])
@pytest.mark.parametrize("token_source", ["argument", "environment"])
def test_bearer_http_nonloopback_refused_before_transport(wire, monkeypatch, asynchronous, source, token_source):
    url = "http://bearer-transport.invalid/omega/api"
    options = {"base_url": "https://base-transport.invalid"}
    if token_source == "environment":
        monkeypatch.setenv("FI_PLATFORM_TOKEN", TOKEN)
        options["platform_token"] = None
    if source == "argument":
        options["platform_base_url"] = url
    elif source == "environment":
        monkeypatch.setenv("FI_PLATFORM_BASE_URL", url)
    else:
        options["base_url"] = "http://bearer-transport.invalid"
    c = wire.client(asynchronous, "bearer", **options)
    try:
        with pytest.raises(errors.ConfigurationError) as caught:
            run(asynchronous, lambda: c.environments.list())
        assert wire.requests == []
        assert "http" in str(caught.value).lower()
        assert "allow_insecure_http" in str(caught.value) or "FI_ALLOW_INSECURE_HTTP" in str(caught.value)
        assert_private(caught.value)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("base", ["http://localhost:19876", "http://127.0.0.1:19876", "http://[::1]:19876", "https://secure-transport.invalid"])
@pytest.mark.parametrize("mode", ["keys", "bearer"])
def test_loopback_and_https_need_no_http_opt_in(wire, capsys, caplog, asynchronous, base, mode):
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        c = wire.client(asynchronous, mode, retries=0, base_url=base)
        try:
            run(asynchronous, lambda: c.environments.list())
            assert_selected_only(wire, base, mode, 1)
        finally:
            close(c, asynchronous)
    assert warning_texts(recorded, capsys, caplog) == []


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("flag", ["argument", "environment"])
def test_named_bearer_optout_warns_once_per_origin_and_survives_clone(
    wire, monkeypatch, capsys, caplog, asynchronous, flag,
):
    host = "bearer-opt-in-" + uuid4().hex + ".invalid"
    if flag == "environment":
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    options = {"allow_insecure_http": True} if flag == "argument" else {}
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        # Same canonical origin despite two paths and explicit default port;
        # different port is genuinely another origin and must warn separately.
        for url in (f"http://{host}/private-path/a", f"http://{host}:80/private-path/b", f"http://{host}:8080/private-path/c"):
            c = wire.client(asynchronous, "bearer", platform_base_url=url, **options)
            clone = c.with_options(retries=0)  # no invented clone auth/URL parameters
            try:
                for caller in (c, clone):
                    run(asynchronous, lambda: caller.environments.list())
            finally:
                close(clone, asynchronous)
                close(c, asynchronous)
    assert len(wire.requests) == 6
    assert all(r.headers.get("authorization") == "Bearer " + TOKEN for r in wire.requests)
    assert_warning_safety(warning_texts(recorded, capsys, caplog), 1)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("scope", ["core", "console"])
def test_keys_http_with_the_opt_in_warns_once(wire, monkeypatch, capsys, caplog, asynchronous, scope):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    host = "keys-transport-" + uuid4().hex + ".invalid"
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        for base in (f"http://{host}/private-path/a", f"http://{host}:80/private-path/b", f"http://{host}:8080/private-path/c"):
            c = wire.client(asynchronous, retries=0, base_url=base)
            try:
                for _ in range(2):
                    run(asynchronous, lambda: invoke(c, asynchronous, scope))
            finally:
                close(c, asynchronous)
    assert len(wire.requests) == 6
    assert all(r.headers.get("x-api-key") == API_KEY and r.headers.get("x-secret-key") == SECRET_KEY for r in wire.requests)
    assert_warning_safety(warning_texts(recorded, capsys, caplog), 1, keys=True)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_explicit_http_platform_warns_with_https_core_base(wire, monkeypatch, capsys, caplog, asynchronous):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    base = "http://explicit-transport-" + uuid4().hex + ".invalid"
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        c = wire.client(asynchronous, retries=0, base_url="https://core-transport.invalid",
                        platform_base_url=base + "/omega/api")
        try:
            for _ in range(2):
                run(asynchronous, lambda: c.environments.list())
            assert_selected_only(wire, base, "keys", 2)
        finally:
            close(c, asynchronous)
    assert_warning_safety(warning_texts(recorded, capsys, caplog), 1, keys=True)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_custom_host_optout_is_not_the_insecure_http_optout(wire, asynchronous):
    c = wire.client(asynchronous, "bearer", base_url="http://custom-transport.invalid", allow_custom_platform_url=True)
    try:
        with pytest.raises(errors.ConfigurationError):
            run(asynchronous, lambda: c.environments.list())
        assert wire.requests == []
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("flag", ["argument", "environment"])
@pytest.mark.parametrize("mode", ["keys", "bearer"])
@pytest.mark.skipif(SANDBOX_ABSENT, reason=NOT_APPLICABLE_AT_FOLD)
def test_global_optout_does_not_weaken_sandbox_policy(wire, monkeypatch, asynchronous, flag, mode):
    if flag == "environment":
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    options = {"allow_insecure_http": True} if flag == "argument" else {}
    c = wire.client(asynchronous, mode, base_url="http://sandbox-transport.invalid", **options)
    try:
        with pytest.raises(errors.ConfigurationError) as caught:
            run(asynchronous, lambda: c.sandboxes.list())
        assert caught.value.code == "insecure_sandbox_origin"
        assert wire.requests == []
        assert_private(caught.value)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("source", ["arguments", "environment"])
def test_mixed_credentials_precede_new_scheme_refusal_for_valid_url(wire, monkeypatch, asynchronous, source):
    options = {"base_url": "http://mixed-transport.invalid"}
    if source == "arguments":
        options.update(api_key=API_KEY, secret_key=SECRET_KEY)
    else:
        monkeypatch.setenv("FI_API_KEY", API_KEY)
        monkeypatch.setenv("FI_SECRET_KEY", SECRET_KEY)
    c = wire.client(asynchronous, "bearer", **options)
    try:
        with pytest.raises(errors.MixedCredentialsError) as caught:
            run(asynchronous, lambda: c.environments.list())
        assert caught.value.code == "mixed_credentials"
        assert wire.requests == []
        assert_private(caught.value)
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
def test_does_not_assert_mixed_precedence_over_malformed_urls(wire, asynchronous):
    c = wire.client(asynchronous, "bearer", api_key=API_KEY, secret_key=SECRET_KEY,
                    platform_base_url="https://invalid-transport.invalid/?query=not-an-origin")
    try:
        with pytest.raises(errors.PlatformNotConfiguredError):
            run(asynchronous, lambda: c.environments.list())
        assert wire.requests == []
    finally:
        close(c, asynchronous)


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("scope,mode", [("core", "keys"), ("console", "keys"), ("console", "bearer")])
@pytest.mark.parametrize("base,other", [(US, EU), (EU, US)])
@pytest.mark.parametrize("retries", [None, 0], ids=["default-retries", "retries-zero"])
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@pytest.mark.parametrize("downgrade", [False, True])
def test_non_sandbox_transports_refuse_redirects(
    wire, asynchronous, scope, mode, base, other, retries, status, downgrade,
):
    target = (base.replace("https://", "http://") if downgrade else other) + "/untrusted-path?not-a-key=synthetic-marker"
    wire.respond = lambda r: httpx.Response(status, headers={"location": target})
    c = wire.client(asynchronous, mode, retries, base_url=base)
    try:
        with pytest.raises(errors.UnexpectedRedirectError) as caught:
            run(asynchronous, lambda: invoke(c, asynchronous, scope))
        assert_selected_only(wire, base, mode, 1)
        assert wire.sleeps == []
        # Existing non-sandbox policy may name the target host, not URL/path/query.
        assert target not in str(caught.value)
        assert "synthetic-marker" not in str(caught.value)
        assert API_KEY not in str(caught.value) and SECRET_KEY not in str(caught.value) and TOKEN not in str(caught.value)
    finally:
        close(c, asynchronous)
