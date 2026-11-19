"""FI_EXTRA_HEADERS / extra_headers=: parsing, precedence, scope and secrecy (fi._extra_headers).

No network: the clients' wiring is checked with httpx.MockTransport and fake requests objects here;
tests/test_extra_headers_integration.py sends real requests to local 127.0.0.1 servers.
"""

from __future__ import annotations

import httpx
import pytest

from fi import _extra_headers as xh
from fi._extra_headers import ENV_VAR, ExtraHeaders, ExtraHeadersError

# a made-up value, low entropy on purpose (never a real token)
TOKEN = "fake-identity-token-" + "x" * 12
VALUE = f"Bearer {TOKEN}"


@pytest.fixture(autouse=True)
def _no_setting(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)


# -- parsing --


def test_parse_semicolons_newlines_spaces_and_equals_in_value():
    text = f" Proxy-Authorization = {VALUE} ;\n\nX-Team=india\r\nX-Sig=a=b== ;"
    assert xh.parse(text) == {"Proxy-Authorization": VALUE, "X-Team": "india", "X-Sig": "a=b=="}


def test_parse_empty_and_blank_is_nothing():
    assert xh.parse("") == {}
    assert xh.parse(" ;\n ; ") == {}
    assert xh.from_env({ENV_VAR: ""}) == {}
    assert xh.from_env({}) == {}


@pytest.mark.parametrize(
    "text, words",
    [
        (f"Proxy-Authorization {VALUE}", ["entry 1", "no '='"]),
        (f"Proxy-Authorization: {VALUE}=x", ["entry 1", "not a valid HTTP header name"]),
        (f"Bad Name={TOKEN}", ["not a valid HTTP header name"]),
        ("X-Ok=1;=nothing", ["entry 2", "not a valid HTTP header name"]),
        ("X-Empty=", ["entry 1", "X-Empty", "empty"]),
        ("Proxy-Authorization=Bearer", ["only an auth scheme", "token variable empty"]),
        ("Proxy-Authorization=bearer ", ["only an auth scheme"]),
        ("X-Uni=café", ["X-Uni", "not visible ASCII"]),
        ("X-Ctl=a\x00b", ["X-Ctl", "not visible ASCII"]),
        (f"X-Dup=1;x-dup={TOKEN}", ["entry 2", "x-dup", "given twice"]),
    ],
)
def test_parse_errors_name_the_setting_and_entry_never_the_value(text, words):
    with pytest.raises(ExtraHeadersError) as info:
        xh.parse(text)
    message = str(info.value)
    assert message.startswith(ENV_VAR)
    for word in words:
        assert word in message
    assert TOKEN not in message and TOKEN not in repr(info.value)
    assert info.value.get_error_code() == "EXTRA_HEADERS_INVALID"
    assert isinstance(info.value, ValueError)


@pytest.mark.parametrize("name", ["X-Api-Key", "x-secret-key", "AUTHORIZATION", "Authorization"])
def test_the_sdk_auth_headers_are_refused_by_name(name):
    with pytest.raises(ExtraHeadersError) as info:
        xh.parse(f"{name}={TOKEN}")
    message = str(info.value)
    assert ENV_VAR in message and name in message and "cannot be set" in message
    assert TOKEN not in message
    with pytest.raises(ExtraHeadersError) as info:
        xh.validate({name: TOKEN})
    assert "extra_headers=" in str(info.value) and TOKEN not in str(info.value)


def test_proxy_authorization_is_allowed():
    assert xh.parse(f"Proxy-Authorization={VALUE}") == {"Proxy-Authorization": VALUE}


def test_validate_mapping_string_and_wrong_types():
    assert xh.validate({"X-A": " 1 "}) == {"X-A": "1"}
    assert xh.validate("X-A=1;X-B=2") == {"X-A": "1", "X-B": "2"}
    assert xh.validate(None) == {}
    with pytest.raises(ExtraHeadersError, match="mapping"):
        xh.validate([("X-A", "1")])  # type: ignore[arg-type]
    with pytest.raises(ExtraHeadersError, match="must be a string"):
        xh.validate({"X-A": 1})  # type: ignore[dict-item]
    with pytest.raises(ExtraHeadersError, match="given twice"):
        xh.validate({"X-A": "1", "x-a": "2"})


# -- precedence --


def test_argument_wins_over_the_setting_per_name_without_case():
    env = {ENV_VAR: f"Proxy-Authorization={VALUE};X-Team=env"}
    got = xh.resolve({"x-team": "arg", "X-Extra": "1"}, environ=env)
    assert got == {"Proxy-Authorization": VALUE, "x-team": "arg", "X-Extra": "1"}
    assert xh.resolve(None, environ=env) == {"Proxy-Authorization": VALUE, "X-Team": "env"}
    assert xh.resolve("X-Team=arg2", environ=env)["X-Team"] == "arg2"


def test_a_bad_argument_fails_when_the_client_is_built(monkeypatch):
    with pytest.raises(ExtraHeadersError, match="extra_headers= entry 1"):
        ExtraHeaders("http://127.0.0.1:1", {"X-Api-Key": "k"})


def test_the_setting_is_read_when_each_request_is_sent(monkeypatch):
    extra = ExtraHeaders("http://127.0.0.1:1/api", {"X-Arg": "a"})
    assert extra.for_url("http://127.0.0.1:1/api/x") == {"X-Arg": "a"}
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE}")
    assert extra.for_url("http://127.0.0.1:1/api/x") == {"Proxy-Authorization": VALUE, "X-Arg": "a"}
    monkeypatch.setenv(ENV_VAR, "Proxy-Authorization=Bearer refreshed-token-0001")
    assert extra.for_url("http://127.0.0.1:1/api/x")["Proxy-Authorization"] == "Bearer refreshed-token-0001"
    monkeypatch.setenv(ENV_VAR, "broken")
    with pytest.raises(ExtraHeadersError):
        extra.for_url("http://127.0.0.1:1/api/x")
    assert extra.for_url("http://127.0.0.2:1/api/x") == {}  # off the base URL the setting is not even read


def test_apply_keeps_a_header_the_caller_set():
    extra = ExtraHeaders("https://team.example", {"X-Team": "arg", "X-New": "1"})
    headers = {"x-team": "explicit"}
    extra.apply(headers, "https://team.example/model-hub/x")
    assert headers == {"x-team": "explicit", "X-New": "1"}


# -- scope --


@pytest.mark.parametrize(
    "url, base, ok",
    [
        ("https://team.example/x", "https://team.example", True),
        ("https://TEAM.example:443/x", "https://team.example/", True),
        ("https://team.example/api/v1", "https://team.example/api", True),
        ("https://team.example/api", "https://team.example/api/", True),
        ("https://team.example/apix", "https://team.example/api", False),
        ("https://team.example/other", "https://team.example/api", False),
        ("http://team.example/x", "https://team.example", False),
        ("https://team.example:8443/x", "https://team.example", False),
        ("https://evil.example/x", "https://team.example", False),
        ("https://team.example.evil.example/x", "https://team.example", False),
        ("https://user@evil.example/x", "https://team.example", False),
        ("http://127.0.0.1:9/x", "http://127.0.0.1:8/", False),
        ("/relative/path", "https://team.example", False),
        ("ftp://team.example/x", "ftp://team.example", False),
        ("https://team.example:notaport/x", "https://team.example", False),
    ],
)
def test_on_platform(url, base, ok):
    assert xh.on_platform(url, base) is ok


# -- secrecy --


def test_repr_describe_and_secret_values_never_show_values(monkeypatch):
    extra = ExtraHeaders("https://team.example", {"Proxy-Authorization": VALUE})
    assert TOKEN not in repr(extra) and "Proxy-Authorization" in repr(extra)
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE};X-Team=india-team")
    assert xh.describe() == {"names": ["Proxy-Authorization", "X-Team"], "source": ENV_VAR}
    assert set(xh.secret_values()) == {VALUE, TOKEN, "india-team"}
    assert xh.secret_values(extra=[{"X-Arg": "argument-value-1"}])[0] in (VALUE, "argument-value-1")
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization {VALUE}")
    described = xh.describe()
    assert described["names"] == [] and "no '='" in described["error"] and TOKEN not in described["error"]
    assert xh.secret_values() == []  # malformed: the redactor still has the whole raw setting (FI_*)
    monkeypatch.delenv(ENV_VAR)
    assert xh.describe() == {"names": [], "source": None}


# -- wiring, without a network --


def _mock_client(handler, extra, base="http://platform.test"):
    from fi._credentials import Credentials
    from fi._http import LazyKeyAuth

    creds = Credentials(api_key="ak", secret_key="sk", base_url=base, base_url_source="argument",
                        keys_source="argument")
    auth = LazyKeyAuth(lambda: creds, extra=extra)
    return httpx.Client(base_url=base, auth=auth, transport=httpx.MockTransport(handler))


def test_lazy_key_auth_adds_the_headers_on_platform_urls_only(monkeypatch):
    seen = []

    def handler(request):
        seen.append((str(request.url), dict(request.headers)))
        return httpx.Response(200, json={})

    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE}")
    with _mock_client(handler, ExtraHeaders("http://platform.test", {"X-Team": "t"})) as client:
        client.get("/model-hub/x")
        client.get("http://elsewhere.test/y")
        client.get("/z", headers={"X-Team": "explicit"})
    (u1, h1), (u2, h2), (u3, h3) = seen
    assert h1["proxy-authorization"] == VALUE and h1["x-team"] == "t" and h1["x-api-key"] == "ak"
    assert "proxy-authorization" not in h2 and "x-team" not in h2
    assert h3["x-team"] == "explicit" and h3["proxy-authorization"] == VALUE


def test_doctor_shows_names_never_values(monkeypatch, capsys, tmp_path):
    import json

    from fi._cli.main import main

    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "none.json"))
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE};X-Team=india-team")
    assert main(["doctor", "--offline"]) == 0
    out = capsys.readouterr()
    assert "Headers    Proxy-Authorization, X-Team  (from FI_EXTRA_HEADERS; sent to http://127.0.0.1:9 only)" in out.out
    assert TOKEN not in out.out + out.err and "india-team" not in out.out + out.err
    assert main(["doctor", "--offline", "--json"]) == 0
    raw = capsys.readouterr().out
    assert TOKEN not in raw and "india-team" not in raw
    assert json.loads(raw)["extra_headers"] == {"names": ["Proxy-Authorization", "X-Team"], "source": ENV_VAR}
    monkeypatch.setenv(ENV_VAR, f"X-Api-Key={TOKEN}")
    assert main(["doctor", "--offline", "--json"]) == 3
    raw = capsys.readouterr().out
    assert TOKEN not in raw and "X-Api-Key cannot be set" in json.loads(raw)["extra_headers"]["error"]
