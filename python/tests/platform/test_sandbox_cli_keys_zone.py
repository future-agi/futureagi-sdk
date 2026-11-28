"""The ``sandbox`` command line sends the exported key pair only to a Future AGI host or loopback. A
``--base-url`` outside the zone is refused before
any request, with exit 2 and one line naming the flag that allows it and the self-host variable,
unless ``--allow-custom-base-url`` is also passed. FI_ALLOW_CUSTOM_PLATFORM_URL applies to
OMEGA_BASE_URL, not an explicit ``--base-url``, as for ``Sandbox.create``. The flag is the command-line form of
``allow_custom_base_url``, so it also lets a self-host token reach an EE that is not on loopback.
Sending the key pair off the zone prints the core's notice on stderr; a self-host token prints none.
``sandbox mcp`` follows the same rule with the same refusal text (``mcp`` is faked). Fake
credentials only."""

from __future__ import annotations

import pytest
from fi._core import origins

from tests.sandbox_integrations import _fake_mcp

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    LOCAL,
    names,
    no_secret,
    run,
    server_fixture,
)
from ._sandbox_mock import FAKE_KEY, FAKE_SECRET, FAKE_TOKEN, HOSTED, SBX

OTHER_ORIGIN = "https://other-origin.example/omega/api"
NOTICE = "futureagi: sending your keys to other-origin.example, outside the Future AGI zone"


@pytest.fixture(name="hosted")
def hosted_fixture(server, monkeypatch):
    """The exported Future AGI key pair (no token); the server fixture's loopback OMEGA_BASE_URL."""
    monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY")
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    monkeypatch.setattr(origins, "_warned", set())
    return server


def refusal_line(capsys):
    captured = capsys.readouterr()
    assert captured.out == ""
    no_secret(captured.out, captured.err)
    lines = captured.err.splitlines()
    assert len(lines) == 1, captured.err
    return lines[0]


@pytest.mark.parametrize("argv", [
    ("--base-url", OTHER_ORIGIN, "list"),
    ("list", "--base-url", OTHER_ORIGIN),
    ("get", SBX, "--base-url", "https://other-origin.example:8443"),
    ("--base-url", "https://futureagi.com.other-origin.example/omega/api", "create"),
])
def test_a_typed_base_url_outside_the_zone_is_refused_before_any_request(hosted, capsys, argv):
    assert run(*argv) == 2
    line = refusal_line(capsys)
    assert line.startswith("custom_base_url_not_allowed: "), line
    assert "Future AGI hosts" in line and "--allow-custom-base-url" in line
    assert "FUTUREAGI_OMEGA_API_KEY" in line and "FI_ALLOW_CUSTOM_PLATFORM_URL" not in line
    assert "other-origin.example" in line and "/omega/api" not in line
    assert hosted.seen == []


def test_the_environment_opt_in_never_opens_a_typed_base_url(hosted, capsys, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("--base-url", OTHER_ORIGIN, "list") == 2
    assert refusal_line(capsys).startswith("custom_base_url_not_allowed: ")
    assert hosted.seen == []


@pytest.mark.parametrize("argv", [
    ("--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "list"),
    ("--allow-custom-base-url", "list", "--base-url", OTHER_ORIGIN),
    ("list", "--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "--json"),
])
def test_the_flag_sends_them_there_and_prints_the_core_notice_once(hosted, capsys, argv):
    assert run(*argv) == 0
    assert run(*argv) == 0
    assert names(hosted) == ["sandboxes.list"] * 2
    assert all(str(seen.request.url).startswith("https://other-origin.example/omega/api/") for seen in hosted.seen)
    assert hosted.last.request.headers["x-api-key"] == FAKE_KEY
    captured = capsys.readouterr()
    assert captured.err.count(NOTICE) == 1
    no_secret(captured.out, captured.err)


def test_an_omega_base_url_outside_the_zone_names_both_ways_to_allow_it(hosted, capsys, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", OTHER_ORIGIN)
    assert run("list") == 2
    line = refusal_line(capsys)
    assert line.startswith("custom_base_url_not_allowed: ")
    assert "--allow-custom-base-url" in line and "FI_ALLOW_CUSTOM_PLATFORM_URL=1" in line
    assert hosted.seen == []
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("list") == 0
    assert names(hosted) == ["sandboxes.list"] and NOTICE in capsys.readouterr().err


@pytest.mark.parametrize("base", [HOSTED, "http://127.0.0.1:9911", "http://localhost:9912"])
def test_a_future_agi_host_or_loopback_needs_no_flag(hosted, capsys, base):
    assert run("--base-url", base, "list") == 0
    assert str(hosted.last.request.url).startswith(base + "/workspace/sandboxes")
    assert hosted.last.request.headers["x-api-key"] == FAKE_KEY
    assert capsys.readouterr().err == ""


def test_the_flag_lets_a_self_host_token_reach_an_ee_off_loopback(server, capsys):
    assert run("--base-url", "https://ee.example.test", "list") == 2
    assert "--allow-custom-base-url" in refusal_line(capsys)
    assert server.seen == []
    assert run("--base-url", "https://ee.example.test", "--allow-custom-base-url", "list") == 0
    assert server.last.request.headers["authorization"] == f"Bearer {FAKE_TOKEN}"
    assert str(server.last.request.url).startswith("https://ee.example.test/workspace/sandboxes")


def test_the_flag_never_allows_plain_http_off_loopback(hosted, capsys):
    assert run("--base-url", "http://other-origin.example/omega/api", "--allow-custom-base-url", "list") == 2
    assert refusal_line(capsys).startswith("insecure_sandbox_origin: ")
    assert hosted.seen == []


def test_help_states_the_host_rule(server, capsys):
    assert run("--help") == 0
    out = " ".join(capsys.readouterr().out.split())
    assert "--allow-custom-base-url" in out and "Future AGI hosts" in out and "loopback" in out


def test_exec_accepts_the_flag_before_the_dashes(server, capsys):
    assert run("exec", "--allow-custom-base-url", SBX, "--", "true") == 0
    assert names(server) == ["sandboxes.commands.run"]
    assert LOCAL in str(server.last.request.url)


def test_help_says_when_the_flag_prints_a_notice(server, capsys, monkeypatch):
    monkeypatch.setenv("COLUMNS", "100")  # argparse wraps help to the terminal: keep each name whole
    for argv in (("--help",), ("mcp", "--help")):
        assert run(*argv) == 0
        out = " ".join(capsys.readouterr().out.split())
        assert "(prints a notice)" not in out
        assert "(FI_API_KEY, FI_SECRET_KEY) there prints a notice on stderr" in out
        assert "FUTUREAGI_OMEGA_API_KEY token is sent with no notice" in out


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
    ("mcp", "--base-url", OTHER_ORIGIN),
    ("--base-url", OTHER_ORIGIN, "mcp"),
])
def test_mcp_refuses_a_typed_base_url_outside_the_zone_before_any_request(hosted, mcp, capsys, argv):
    assert run("--base-url", OTHER_ORIGIN, "list") == 2
    listed = refusal_line(capsys)
    assert run(*argv) == 2
    assert refusal_line(capsys) == listed
    assert listed.startswith("custom_base_url_not_allowed: ") and "--allow-custom-base-url" in listed
    assert "FI_ALLOW_CUSTOM_PLATFORM_URL" not in listed
    assert hosted.seen == [] and mcp.instances == []


def test_mcp_never_lets_the_environment_opt_in_open_a_typed_base_url(hosted, mcp, capsys, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("mcp", "--base-url", OTHER_ORIGIN) == 2
    assert refusal_line(capsys).startswith("custom_base_url_not_allowed: ")
    assert hosted.seen == [] and mcp.instances == []


def test_mcp_follows_the_variable_for_an_omega_base_url(hosted, mcp, capsys, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", OTHER_ORIGIN)
    assert run("list") == 2
    listed = refusal_line(capsys)
    assert run("mcp") == 2
    assert refusal_line(capsys) == listed
    assert "--allow-custom-base-url" in listed and "FI_ALLOW_CUSTOM_PLATFORM_URL=1" in listed
    assert hosted.seen == [] and mcp.instances == []
    monkeypatch.setenv("FI_ALLOW_CUSTOM_PLATFORM_URL", "1")
    assert run("mcp") == 0
    assert names(hosted) == ["sandboxes.list"]
    assert str(hosted.last.request.url).startswith(OTHER_ORIGIN + "/")
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.count(NOTICE) == 1
    no_secret(captured.out, captured.err)


@pytest.mark.parametrize("argv", [
    ("mcp", "--base-url", OTHER_ORIGIN, "--allow-custom-base-url"),
    ("--allow-custom-base-url", "mcp", "--base-url", OTHER_ORIGIN),
    ("--base-url", OTHER_ORIGIN, "--allow-custom-base-url", "mcp"),
])
def test_mcp_passes_the_flag_through_for_the_key_pair(hosted, mcp, capsys, argv):
    assert run(*argv) == 0
    assert [srv.runs for srv in mcp.instances] == [1]
    assert names(hosted) == ["sandboxes.list"]
    assert str(hosted.last.request.url).startswith(OTHER_ORIGIN + "/")
    assert hosted.last.request.headers["x-api-key"] == FAKE_KEY
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.count(NOTICE) == 1
    no_secret(captured.out, captured.err)


def test_mcp_passes_the_flag_through_for_a_self_host_token(server, mcp, capsys):
    assert run("mcp", "--base-url", "https://ee.example.test") == 2
    line = refusal_line(capsys)
    assert line.startswith("custom_base_url_not_allowed: ") and "--allow-custom-base-url" in line
    assert server.seen == [] and mcp.instances == []
    assert run("mcp", "--base-url", "https://ee.example.test", "--allow-custom-base-url") == 0
    assert names(server) == ["sandboxes.list"]
    assert server.last.request.headers["authorization"] == f"Bearer {FAKE_TOKEN}"
    assert str(server.last.request.url).startswith("https://ee.example.test/workspace/sandboxes")
    assert capsys.readouterr() == ("", "")  # a token gets no notice
