"""The ``sandbox`` command group (contract v1 section 5 with v2 item 6), part 1: registration and
help, usage and configuration errors (2), both credential modes and their scope headers, refusals
(1, ``code: message`` with one next step), and the sandbox commands (list, create, get, hibernate,
resume, delete, settings), against the mock server driven by the frozen OpenAPI. Settings come
from the environment only; fake credentials only. exec: test_sandbox_cli_exec.py; files,
snapshots and the network policy: test_sandbox_cli_files.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from fi._cli import main as cli_main
from fi._cli import registry

from ._sandbox_cli_support import (  # noqa: F401 (registers the server fixture)
    _EP,
    LOCAL,
    answer,
    names,
    no_secret,
    record,
    refuse,
    run,
    server_fixture,
)
from ._sandbox_mock import FAKE_KEY, FAKE_SECRET, FAKE_TOKEN, ORIGIN, SBX, error

# --- registration and help -------------------------------------------------------------------


def test_the_group_is_registered_by_one_line_and_listed_under_platform(monkeypatch):
    assert registry.source_tree_groups().get("sandbox") == "fi._cli.sandbox"
    monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
    parser = cli_main.build_parser(warn=lambda message: None)
    assert "sandbox" in parser.epilog.split("Platform:")[1].split("\n\n")[0]


def test_registering_the_group_loads_neither_the_http_client_nor_the_sandbox_package():
    py_root = Path(__file__).resolve().parents[2]
    code = (
        f"import sys; sys.path.insert(0, {str(py_root)!r})\n"
        "import argparse, fi._cli.sandbox as g\n"
        "g.register(argparse.ArgumentParser().add_subparsers())\n"
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'httpx' or m.startswith('fi.sandbox')))\n"
    )
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]", out


def test_help_explains_the_settings_and_the_exit_codes(server, capsys):
    assert run("--help") == 0
    out = capsys.readouterr().out
    for text in ("OMEGA_BASE_URL", "FI_API_KEY", "FUTUREAGI_OMEGA_API_KEY", "exit codes", "124", "130",
                 "exec", "cp", "network-policy", "snapshot", "saved `login` is not used"):
        assert text in out, text
    assert run("exec", "--help") == 0
    out = capsys.readouterr().out
    assert "--cwd" in out and "--timeout" in out and "pipes" in out
    assert "SANDBOX_ID -- COMMAND" in out and "-- ls -la" in out


@pytest.mark.parametrize("argv", [
    (), ("bogus",), ("create", "--idle-ttl", "soon"), ("create", "--size", "huge"), ("exec", SBX),
    ("exec", SBX, "--env", "NOEQUALS", "--", "ls"), ("exec", SBX, "--timeout", "0", "--", "ls"),
    ("snapshot",), ("snapshot", "restore", SBX), ("network-policy", "set", SBX), ("get",),
    ("list", "--format", "yaml"),
])
def test_bad_flags_are_usage_errors_and_send_nothing(server, capsys, argv):
    assert run(*argv) == 2
    assert server.seen == []


# --- configuration (exit 2) and authentication ------------------------------------------------


def test_no_base_url_names_omega_base_url_and_sends_nothing(server, capsys, monkeypatch):
    monkeypatch.delenv("OMEGA_BASE_URL")
    assert run("list") == 2
    err = capsys.readouterr().err
    assert err.startswith("missing_base_url: ") and "OMEGA_BASE_URL" in err and "--base-url" in err
    assert server.seen == []


def test_base_url_flag_takes_the_place_of_the_environment(server, capsys, monkeypatch):
    monkeypatch.delenv("OMEGA_BASE_URL")
    assert run("--base-url", "http://127.0.0.1:9911", "get", SBX) == 0
    assert str(server.last.request.url) == f"http://127.0.0.1:9911/workspace/sandboxes/{SBX}"
    assert run("get", SBX, "--base-url", "http://localhost:9912") == 0
    assert str(server.last.request.url).startswith("http://localhost:9912/")


def test_both_credential_modes_is_a_configuration_error(server, capsys, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    assert run("list") == 2
    captured = capsys.readouterr()
    assert captured.err.startswith("mixed_credentials: ") and captured.out == ""
    no_secret(captured.out, captured.err)
    assert server.seen == []


@pytest.mark.parametrize("env,code", [
    ({"FUTUREAGI_OMEGA_API_KEY": None}, "missing_credentials"),
    ({"OMEGA_BASE_URL": "https://ee.example.test"}, "custom_base_url_not_allowed"),
    ({"OMEGA_BASE_URL": "http://sbx.example.test/omega/api", "FUTUREAGI_OMEGA_API_KEY": None,
      "FI_API_KEY": FAKE_KEY, "FI_SECRET_KEY": FAKE_SECRET}, "insecure_sandbox_origin"),
    ({"OMEGA_BASE_URL": "not a url"}, "invalid_base_url"),
])
def test_configuration_refusals_exit_2_before_sending(server, capsys, monkeypatch, env, code):
    for name, value in env.items():
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    assert run("create") == 2
    captured = capsys.readouterr()
    assert captured.err.startswith(f"{code}: "), captured.err
    no_secret(captured.out, captured.err)
    assert server.seen == []


def test_a_foreign_self_host_refusal_speaks_to_a_command_line_user(server, capsys, monkeypatch):
    monkeypatch.setenv("OMEGA_BASE_URL", "https://ee.example.test")
    assert run("list") == 2
    err = capsys.readouterr().err
    assert "loopback" in err and "allow_custom_base_url" in err


def test_hosted_keys_and_scope_headers_by_mode(server, capsys, monkeypatch):
    monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY")
    monkeypatch.setenv("OMEGA_BASE_URL", ORIGIN)
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    monkeypatch.setenv("FI_WORKSPACE_ID", "ws_1")
    monkeypatch.setenv("FI_ORGANIZATION_ID", "org_1")
    assert run("list") == 0
    headers = server.last.request.headers
    assert headers["x-api-key"] == FAKE_KEY and headers["x-secret-key"] == FAKE_SECRET
    assert headers["x-workspace-id"] == "ws_1" and headers["x-organization-id"] == "org_1"
    assert "authorization" not in headers and "x-omega-workspace" not in headers
    assert str(server.last.request.url).startswith(ORIGIN + "/workspace/sandboxes")
    no_secret(*capsys.readouterr())


def test_self_host_bearer_and_scope_headers_by_mode(server, capsys, monkeypatch):
    monkeypatch.setenv("FI_WORKSPACE_ID", "ws_2")
    monkeypatch.setenv("FI_ORGANIZATION_ID", "org_2")
    assert run("list") == 0
    headers = server.last.request.headers
    assert headers["authorization"] == f"Bearer {FAKE_TOKEN}"
    assert headers["x-omega-workspace"] == "ws_2" and headers["x-omega-org"] == "org_2"
    assert "x-api-key" not in headers and "x-workspace-id" not in headers
    no_secret(*capsys.readouterr())


def test_a_missing_credential_says_a_saved_login_is_not_read(server, capsys, monkeypatch):
    monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY")
    assert run("list") == 2
    err = capsys.readouterr().err
    assert err.startswith("missing_credentials: ") and "saved login is not read" in err
    assert server.seen == []


def test_an_unreachable_server_names_the_setting_this_command_reads(server, capsys, monkeypatch):
    import fi._http

    monkeypatch.setattr(fi._http, "backoff_s", lambda *args: 0)

    def refused(request):
        raise httpx.ConnectError("refused", request=request)

    server.on("sandboxes.list", refused)
    assert run("list") == 1
    err = capsys.readouterr().err
    assert err.startswith("server_unreachable: ") and "OMEGA_BASE_URL (or --base-url)" in err
    assert "FI_PLATFORM_BASE_URL" not in err


# --- refusals (exit 1) -----------------------------------------------------------------------


@pytest.mark.parametrize("fmt", [(), ("--json",)])
def test_a_refusal_prints_code_and_message_and_exits_1(server, capsys, fmt):
    server.on("sandboxes.getInfo", refuse(404, "not_found"))
    assert run("get", SBX, *fmt) == 1
    captured = capsys.readouterr()
    assert captured.err.startswith("not_found: ") and captured.out == ""
    no_secret(captured.err)


def test_a_hibernated_sandbox_says_how_to_resume_it(server, capsys):
    server.on("sandboxes.files.list", refuse(409, "sandbox_hibernated", detail={"state": "hibernated"}))
    assert run("ls", SBX) == 1
    err = capsys.readouterr().err
    assert err.startswith("sandbox_hibernated: ") and f"resume {SBX}" in err
    assert names(server) == ["sandboxes.files.list"]


def test_a_dropped_connection_on_a_change_says_completion_is_unknown(server, capsys):
    def drop(request):
        raise httpx.ReadTimeout("slow", request=request)

    server.on("sandboxes.create", drop)
    assert run("create", "--name", "n") == 1
    err = capsys.readouterr().err
    assert "unknown" in err and names(server) == ["sandboxes.create"]
    assert "list the sandboxes before repeating it" in err and "retry" not in err


@pytest.mark.parametrize("status,code,headers,says", [
    (429, "rate_limited", {"Retry-After": "7"}, "Try again in 7 s"),
    (401, "unauthorized", {}, "did not accept FUTUREAGI_OMEGA_API_KEY"),
    (403, "forbidden", {}, "Check FI_WORKSPACE_ID"),
    (404, "not_found", {}, f"No sandbox {SBX} here"),
    (507, "insufficient_storage", {}, "Free some space"),
])
def test_a_refusal_says_what_to_do_next_in_the_servers_words(server, capsys, status, code, headers, says):
    server.on("sandboxes.hibernate", answer(status, json={"code": code, "message": "no."}, headers=headers))
    assert run("hibernate", SBX) == 1
    err = capsys.readouterr().err
    assert err.startswith(f"{code}: no. ") and says in err, err
    assert "failed with status" not in err and "sandboxes.hibernate" not in err
    assert names(server) == ["sandboxes.hibernate"]


def test_a_rejected_key_pair_is_named_with_the_deployment_it_belongs_to(server, capsys, monkeypatch):
    monkeypatch.delenv("FUTUREAGI_OMEGA_API_KEY")
    monkeypatch.setenv("FI_API_KEY", FAKE_KEY)
    monkeypatch.setenv("FI_SECRET_KEY", FAKE_SECRET)
    server.on("sandboxes.list", refuse(401, "unauthorized"))
    assert run("list") == 1
    err = capsys.readouterr().err
    assert "FI_API_KEY and FI_SECRET_KEY" in err and "OMEGA_BASE_URL" in err
    no_secret(err)


# --- sandboxes -------------------------------------------------------------------------------


@pytest.mark.parametrize("fmt", [("--format", "json", "list"), ("list", "--json"), ("list", "--format", "json"),
                                 ("--json", "list")])
def test_list_json_prints_the_api_record_with_the_flag_anywhere(server, capsys, fmt):
    assert run(*fmt) == 0
    body = json.loads(capsys.readouterr().out)
    assert body["sandboxes"][0]["id"] == SBX and "caps" in body
    assert names(server) == ["sandboxes.list"]


def test_list_text_is_a_table_and_an_empty_list_says_how_to_start(server, capsys):
    assert run("list") == 0
    out = capsys.readouterr().out
    assert out.splitlines()[0].split() == ["ID", "NAME", "STATE", "SIZE", "LAST", "ACTIVE"]
    assert SBX in out
    server.on("sandboxes.list", answer(200, json={"schemaVersion": "v1", "sandboxes": [], "caps": {},
                                                          "provider": {}}))
    assert run("list") == 0
    captured = capsys.readouterr()
    assert captured.out == "" and "create --name" in captured.err


def test_create_prints_only_the_id_and_sends_the_flags(server, capsys):
    server.on("sandboxes.create", answer(201, json=record()))
    assert run("create", "--name", "scratch", "--template", "python", "--size", "small", "--idle-ttl", "600") == 0
    assert capsys.readouterr().out == SBX + "\n"
    assert server.last.json() == {"name": "scratch", "template": "python", "size": "small", "idleTtlSeconds": 600}
    assert run("create") == 0
    assert server.last.json() == {}
    assert names(server) == ["sandboxes.create", "sandboxes.create"]


def test_create_json_prints_the_sandbox_record(server, capsys):
    server.on("sandboxes.create", answer(201, json=record(template="python")))
    assert run("create", "--json") == 0
    assert json.loads(capsys.readouterr().out) == record(template="python")["sandbox"]


def test_get_text_and_json(server, capsys):
    server.on("sandboxes.getInfo", answer(200, json=record(size="small")))
    assert run("get", SBX) == 0
    out = capsys.readouterr().out
    assert "ID: " in out and SBX in out and "State:" in out and "active" in out and "small" in out
    assert run("get", SBX, "--format", "json") == 0
    assert json.loads(capsys.readouterr().out) == record(size="small")["sandbox"]
    assert str(server.last.request.url) == f"{LOCAL}/workspace/sandboxes/{SBX}"


@pytest.mark.parametrize("command,operation,state", [
    ("hibernate", "sandboxes.hibernate", "hibernated"),
    ("resume", "sandboxes.resume", "active"),
    ("delete", "sandboxes.kill", "destroyed"),
])
def test_hibernate_resume_and_delete(server, capsys, command, operation, state):
    server.on(operation, answer(200, json=record(state)))
    assert run(command, SBX) == 0
    out = capsys.readouterr().out
    assert (out == f"Deleted {SBX}.\n") if command == "delete" else (out == f"{SBX}: {state}\n")
    assert run(command, SBX, "--json") == 0
    assert json.loads(capsys.readouterr().out)["state"] == state
    assert names(server) == [operation, operation]


def test_delete_of_a_sandbox_that_is_not_here_is_a_refusal_not_a_success(server, capsys):
    server.on("sandboxes.kill", refuse(404, "not_found"))
    assert run("delete", SBX) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.startswith("not_found: ")
    assert f"No sandbox {SBX} here" in captured.err and "FI_WORKSPACE_ID" in captured.err
    assert "sandbox list" in captured.err and names(server) == ["sandboxes.kill"]


def test_delete_that_finds_it_gone_on_a_retry_is_done(server, capsys, monkeypatch):
    import fi._http

    monkeypatch.setattr(fi._http, "backoff_s", lambda *args: 0)
    answers = iter([error(503, "unavailable"), error(404, "not_found")])
    server.on("sandboxes.kill", lambda request: next(answers))
    assert run("delete", SBX, "--json") == 0
    assert json.loads(capsys.readouterr().out) == {"id": SBX, "state": "destroyed"}
    assert names(server) == ["sandboxes.kill", "sandboxes.kill"]


def test_settings_text_and_json(server, capsys):
    assert run("settings") == 0
    captured = capsys.readouterr()
    assert "Templates:" in captured.out and "Sizes:" in captured.out and "Console" in captured.err
    assert run("settings", "--json") == 0
    body = json.loads(capsys.readouterr().out)
    assert {"settings", "caps", "canEdit"} <= set(body)
    assert names(server) == ["sandboxes.settings.get", "sandboxes.settings.get"]
    assert all(seen.request.method == "GET" for seen in server.seen)


def test_settings_lists_the_template_ids_that_create_accepts(server, capsys):
    caps = {"templates": [{"id": "python-data", "name": "Python data"}, {"id": "node", "name": "node"}],
            "sizes": [{"id": "small", "name": "Small"}], "defaultTemplate": "python-data"}
    body = {"schemaVersion": "v1", "settings": {}, "caps": caps, "canEdit": False}
    server.on("sandboxes.settings.get", answer(200, json=body))
    assert run("settings") == 0
    out = capsys.readouterr().out
    assert "python-data (Python data), node" in out and "small (Small)" in out
