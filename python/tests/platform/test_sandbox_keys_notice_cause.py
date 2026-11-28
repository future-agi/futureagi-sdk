"""The core's notice that the key pair is going to a host outside the Future AGI zone names what let
it go there, in the whole line: ``--allow-custom-base-url`` when the ``sandbox`` command line's flag
did (``sandbox mcp`` too, and also with FI_ALLOW_CUSTOM_PLATFORM_URL set, as the flag wins);
FI_ALLOW_CUSTOM_PLATFORM_URL when the variable did (the command line with OMEGA_BASE_URL, and the
environment path under ``Sandbox.create``); ``allow_custom_platform_url=True`` when the client's
argument did. The flag is named only for its own command. Fake credentials only."""

from __future__ import annotations

import pytest
from fi._core import origins
from fi._credentials import resolve as resolve_credentials
from fi.sandbox._connection import resolve_origin

from tests.sandbox_integrations import _fake_mcp

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    names,
    no_secret,
    run,
    server_fixture,
)
from ._sandbox_mock import FAKE_KEY, FAKE_SECRET, FAKE_TOKEN

OTHER_ORIGIN = "https://other-origin.example/omega/api"
LINE = "futureagi: sending your keys to other-origin.example, outside the Future AGI zone, because {}.\n"
BY_FLAG = LINE.format("--allow-custom-base-url was given")
BY_VARIABLE = LINE.format("FI_ALLOW_CUSTOM_PLATFORM_URL is set")
BY_ARGUMENT = LINE.format("allow_custom_platform_url=True was passed")


@pytest.fixture(name="fresh")
def fresh_fixture(monkeypatch):
    """Every test sees the once-per-address notice afresh."""
    monkeypatch.setattr(origins, "_warned", set())


@pytest.fixture(name="hosted")
def hosted_fixture(server, fresh, monkeypatch):
    """Use the Future AGI Cloud key pair (no token) and the fixture's loopback OMEGA_BASE_URL."""
    monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY")
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    return server


def notices(capsys):
    """The key-pair notices on stderr, whole lines; nothing on stderr or stdout holds a key."""
    captured = capsys.readouterr()
    no_secret(captured.out, captured.err)
    return [line for line in captured.err.splitlines(keepends=True) if "sending your keys" in line]


@pytest.mark.parametrize("argv", [
    ("--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "list"),
    ("--allow-custom-base-url", "list", "--base-url", OTHER_ORIGIN),
    ("list", "--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "--json"),
])
def test_the_flag_is_named_when_it_sent_the_keys(hosted, capsys, argv):
    assert run(*argv) == 0
    assert names(hosted) == ["sandboxes.list"]
    assert notices(capsys) == [BY_FLAG]


def test_the_variable_is_named_when_it_sent_the_keys(hosted, capsys, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", OTHER_ORIGIN)
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("list") == 0
    assert names(hosted) == ["sandboxes.list"]
    assert notices(capsys) == [BY_VARIABLE]


def test_the_flag_is_named_when_the_variable_is_also_set(hosted, capsys, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", OTHER_ORIGIN)
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("--allow-custom-base-url", "list") == 0
    assert notices(capsys) == [BY_FLAG]


def test_the_flag_is_named_only_for_its_own_command(hosted, capsys):
    assert run("--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "list") == 0
    assert notices(capsys) == [BY_FLAG]
    origins._warned.clear()
    env = {"OMEGA_BASE_URL": OTHER_ORIGIN, "FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET,
           "FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}
    assert resolve_origin(env).custom is True  # the environment path under Sandbox.create
    assert notices(capsys) == [BY_VARIABLE]


def test_a_command_refused_while_connecting_leaves_no_cause_behind(hosted, capsys, monkeypatch):
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)  # with the key pair: refused
    assert run("--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "list") == 2
    assert notices(capsys) == [] and hosted.seen == []
    env = {"OMEGA_BASE_URL": OTHER_ORIGIN, "FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET,
           "FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}
    assert resolve_origin(env).custom is True
    assert notices(capsys) == [BY_VARIABLE]


# --- sandbox mcp --------------------------------------------------------------------------------


@pytest.fixture(name="mcp")
def mcp_fixture(monkeypatch):
    """The fake MCP framework, with the server module imported afresh; the fake client lists the
    sandboxes once while the server runs."""
    restore = _fake_mcp.isolate_server()
    fake = _fake_mcp.install(monkeypatch)

    async def client(srv):
        await srv.tools["sandbox_list"]()

    fake.on_run = client
    yield fake
    restore()


@pytest.mark.parametrize("argv", [
    ("mcp", "--base-url", OTHER_ORIGIN, "--allow-custom-base-url"),
    ("--allow-custom-base-url", "mcp", "--base-url", OTHER_ORIGIN),
])
def test_mcp_names_the_flag_when_it_sent_the_keys(hosted, mcp, capsys, argv):
    assert run(*argv) == 0
    assert names(hosted) == ["sandboxes.list"]
    assert notices(capsys) == [BY_FLAG]


def test_mcp_names_the_variable_when_it_sent_the_keys(hosted, mcp, capsys, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", OTHER_ORIGIN)
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("mcp") == 0
    assert names(hosted) == ["sandboxes.list"]
    assert notices(capsys) == [BY_VARIABLE]


# --- the client path (FutureAGIClient's origin rule) -------------------------------------------


@pytest.mark.parametrize(("allow", "extra", "line"), [
    (True, {}, BY_ARGUMENT),
    (True, {"FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}, BY_ARGUMENT),
    (None, {"FI_ALLOW_CUSTOM_PLATFORM_URL": "1"}, BY_VARIABLE),
])
def test_the_client_path_names_its_argument_or_the_variable(fresh, tmp_path, capsys, allow, extra, line):
    environ = {"FI_PLATFORM_BASE_URL": OTHER_ORIGIN, **extra}
    creds = resolve_credentials(FAKE_KEY, FAKE_SECRET, None, environ=environ, login_file=tmp_path / "none.json")
    assert origins.resolve_platform(creds, allow_custom_platform_url=allow, environ=environ).custom
    assert notices(capsys) == [line]


def test_the_block_names_its_cause_unless_the_caller_names_one(fresh, tmp_path, capsys):
    env = {"OMEGA_BASE_URL": OTHER_ORIGIN, "FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET}
    other = "https://other.example/omega/api"
    creds = resolve_credentials(FAKE_KEY, FAKE_SECRET, None, environ={"FI_PLATFORM_BASE_URL": other},
                                login_file=tmp_path / "none.json")
    with origins.keys_notice_cause("--allow-custom-base-url was given"):
        assert resolve_origin(env, allow_custom_base_url=True).custom is True
        assert origins.resolve_platform(creds, allow_custom_platform_url=True, environ={}).custom
    assert notices(capsys) == [BY_FLAG, BY_ARGUMENT.replace("other-origin.example", "other.example")]
