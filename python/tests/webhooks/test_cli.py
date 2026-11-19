"""``futureagi-py webhooks`` (unit level): the secret-output rules, header inputs, confirmations, exit codes,
``--json`` shapes and offline ``verify``, with the CLI talking real HTTP to a stub of the API on 127.0.0.1."""

from __future__ import annotations

import base64
import json
import os
import stat
import sys
from pathlib import Path

import pytest

from fi._cli import main as cli_main
from fi._cli import registry

from ._stub import HANGUP, Stub, ok, refuse

SECRET = "whsec_AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
EP = {
    "id": "whep_01", "kind": "http", "name": "hooks.acme.ai", "description": "", "workspace_id": "ws-1",
    "org_wide": False, "url_host": "hooks.acme.ai", "url": "https://hooks.acme.ai/fi", "header_names": [],
    "subscriptions": [{"event_type": "prompt.label.changed", "filters": {}}], "status": "enabled",
    "disabled_reason": None, "disabled_at": None, "payload_mode": "thin", "include_people_names": True,
    "accepts_run_targeting": False, "api_version": "v1", "timeout_ms": 15000, "rate_limit_per_s": 10,
    "max_in_flight": 4, "max_age_s": 259200, "owner_id": "u-1", "created_at": "2026-10-23T00:00:00Z",
    "updated_at": "2026-10-23T00:00:00Z", "can_manage": True, "health": None, "secrets": [],
}
CONF = Path(__file__).resolve().parent / "conformance"


class _EP:
    name = "webhooks"

    def load(self):
        import fi.webhooks._cli as m

        return m


@pytest.fixture
def stub(monkeypatch):
    with Stub() as s:
        monkeypatch.setenv("FI_BASE_URL", s.url)
        monkeypatch.setenv("FI_API_KEY", "k-test")
        monkeypatch.setenv("FI_SECRET_KEY", "s-test")
        monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/login.json")
        monkeypatch.delenv("FI_WORKSPACE_ID", raising=False)
        monkeypatch.setattr(registry, "entry_points", lambda: [_EP()])
        yield s


def run(*argv):
    return cli_main.main(["webhooks", *argv])


def test_the_group_is_registered_by_one_line_and_listed_under_platform():
    groups = registry.source_tree_groups()
    assert groups.get("webhooks") == "fi.webhooks._cli"
    parser = cli_main.build_parser(warn=lambda m: None)
    assert "webhooks" in parser.epilog.split("Platform:")[1].split("\n\n")[0]


def test_registering_the_group_loads_no_http_client_and_no_handler():
    """CLI-49: building the parser (what every ``futureagi-py`` command does) imports neither httpx nor this group's
    handlers, so a broken handler or client module costs only ``futureagi-py webhooks``, never the other commands."""
    import subprocess

    py_root = Path(__file__).resolve().parents[2]
    code = (
        f"import sys; sys.path.insert(0, {str(py_root)!r})\n"
        "import argparse, fi.webhooks._cli as g\n"
        "g.register(argparse.ArgumentParser().add_subparsers())\n"
        "heavy = ('httpx', 'fi.webhooks._client', 'fi.webhooks._cli_run', 'fi.webhooks._cli_log', 'fi.webhooks._cli_io')\n"
        "print(sorted(m for m in sys.modules if m.split('.')[0] == 'httpx' or m in heavy))\n"
    )
    out = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True).stdout
    assert out.strip() == "[]", out


def test_create_refuses_a_non_terminal_stdout_before_any_request(stub, capsys):
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    code = run("create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.label.changed")
    err = capsys.readouterr().err
    assert code == 2 and "--secret-out" in err and stub.seen == []


def test_create_with_secret_out_writes_a_0600_file_and_prints_only_the_tail(stub, capsys, tmp_path):
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    target = tmp_path / "secret.txt"
    target.write_text("old")
    os.chmod(target, 0o644)
    code = run("create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.label.changed",
               "--label", "Production", "--action", "moved", "--secret-out", str(target))
    out, err = capsys.readouterr()
    assert code == 0
    assert target.read_text() == SECRET + "\n"
    assert stat.S_IMODE(os.stat(target).st_mode) == 0o600
    assert SECRET not in out + err and SECRET[-4:] in out
    body = stub.calls("POST", "/webhooks/endpoints/")[0]["body"]
    assert body["subscriptions"] == [{"event_type": "prompt.label.changed",
                                      "filters": {"label_names": ["Production"], "actions": ["moved"]}}]
    assert body["name"] == "hooks.acme.ai"


def test_create_json_shape_with_secret_out(stub, capsys, tmp_path):
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    target = tmp_path / "s"
    assert run("create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.*", "--secret-out", str(target),
               "--json") == 0
    out = json.loads(capsys.readouterr().out)
    assert set(out) == {"endpoint", "warnings", "secret", "secret_file", "secret_tail"}
    assert out["secret"] is None and out["secret_file"] == str(target) and out["endpoint"]["id"] == "whep_01"


def test_a_refused_create_leaves_no_secret_file(stub, capsys, tmp_path):
    stub.on("POST", "/webhooks/endpoints/", refuse(400, "WEBHOOK_URL_UNSAFE_ADDRESS", "url"))
    target = tmp_path / "s"
    code = run("create", "--url", "https://169.254.169.254/", "--event", "prompt.*", "--secret-out", str(target))
    err = capsys.readouterr().err
    assert code == 3 and not target.exists()
    assert "WEBHOOK_URL_UNSAFE_ADDRESS" in err and "(url)" in err


def test_secret_out_that_cannot_be_written_stops_before_any_request(stub, capsys, tmp_path):
    code = run("create", "--url", "https://h.acme.ai/x", "--event", "prompt.*", "--secret-out",
               str(tmp_path / "no" / "such" / "dir"))
    assert code == 2 and stub.seen == [] and "Nothing was sent" in capsys.readouterr().err


def test_show_secret_prints_it_with_a_warning(stub, capsys):
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    assert run("create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.*", "--show-secret") == 0
    out, err = capsys.readouterr()
    assert out.strip().splitlines()[-1] == SECRET and "warning" in err


def test_header_file_and_header_env_values_are_sent_literally(stub, capsys, tmp_path, monkeypatch):
    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    hf = tmp_path / "h.txt"
    hf.write_text("# comment\nAuthorization: Bearer sk-from-file-1\n\nX-Lit: ${INTEGRATION_ENCRYPTION_KEY}\n")
    monkeypatch.setenv("MY_TOKEN", "tok-from-env-2")
    argv = ["create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.*", "--header-file", str(hf),
            "--header-env", "X-Token=MY_TOKEN", "--header", "X-Env: prod", "--show-secret"]
    assert run(*argv) == 0
    assert not any("sk-from-file-1" in a or "tok-from-env-2" in a for a in argv)
    headers = stub.calls("POST", "/webhooks/endpoints/")[0]["body"]["headers"]
    assert headers == {"Authorization": "Bearer sk-from-file-1", "X-Lit": "${INTEGRATION_ENCRYPTION_KEY}",
                       "X-Token": "tok-from-env-2", "X-Env": "prod"}


def test_header_env_naming_an_unset_variable_sends_nothing(stub, capsys, monkeypatch):
    monkeypatch.delenv("NOPE_UNSET", raising=False)
    assert run("create", "--url", "https://h.acme.ai/x", "--event", "prompt.*", "--header-env", "A=NOPE_UNSET",
               "--show-secret") == 2
    assert stub.seen == []


def test_a_filter_flag_that_fits_no_event_is_refused(stub, capsys):
    assert run("create", "--url", "https://h.acme.ai/x", "--event", "deployment.run.completed", "--label", "Prod",
               "--show-secret") == 2
    assert stub.seen == [] and "--label" in capsys.readouterr().err


def test_delete_asks_and_refuses_without_a_terminal(stub, capsys):
    stub.on("DELETE", "/webhooks/endpoints/whep_01/", ok({"deleted": True, "id": "whep_01",
                                                         "cancelled_deliveries": 0}))
    assert run("delete", "whep_01") == 2
    assert stub.seen == [] and "--yes" in capsys.readouterr().err
    assert run("rm", "whep_01", "--yes") == 0
    assert len(stub.calls("DELETE", "/webhooks/endpoints/whep_01/")) == 1


def _test_answer(status_code, outcome="http_error"):
    return ok({"event_id": "evt_test_1", "delivery_id": "dlv_t", "status_code": status_code, "outcome": outcome,
               "latency_ms": 9, "response_excerpt": "<b>hi</b>\u202e"})


def test_test_exits_non_zero_on_a_500_and_zero_on_a_2xx(stub, capsys):
    stub.on("POST", "/webhooks/endpoints/whep_01/test/", _test_answer(500))
    assert run("test", "whep_01", "--event", "prompt.label.changed") == 1
    out, err = capsys.readouterr()
    assert "500" in out and "\\u202e" in out and "\u202e" not in out and "not 2xx" in err
    stub.on("POST", "/webhooks/endpoints/whep_01/test/", _test_answer(204, "success"))
    stub.on("GET", "/webhooks/endpoints/whep_01/", ok(EP))
    assert run("test", "whep_01", "--json") == 0  # the endpoint's only type is picked
    out = json.loads(capsys.readouterr().out)
    assert out["passed"] is True and out["event_type"] == "prompt.label.changed"


def test_test_waits_for_a_202_to_settle(stub, capsys):
    stub.on("POST", "/webhooks/endpoints/whep_01/test/", ok({"event_id": "evt_test_2", "delivery_id": "dlv_u"}, 202))
    polls = []

    def detail(req):
        polls.append(req)
        status = "sending" if len(polls) < 2 else "succeeded"
        attempts = [] if status == "sending" else [{"n": 1, "response_status": 200, "outcome": "success",
                                                    "duration_ms": 20000, "response_body_excerpt": "ok"}]
        return ok({"id": "dlv_u", "status": status, "attempts": attempts})

    stub.on("GET", "/webhooks/deliveries/dlv_u/", detail)
    assert run("test", "whep_01", "--event", "prompt.label.changed", "--wait", "30s") == 0
    assert len(polls) == 2 and "200 success" in capsys.readouterr().out


def test_test_finds_its_delivery_by_event_when_the_202_has_none(stub, capsys):
    stub.on("POST", "/webhooks/endpoints/whep_01/test/", ok({"event_id": "evt_test_3", "delivery_id": None}, 202))
    lists = []

    def by_event(req):
        lists.append(req["query"])
        return ok({"results": [] if len(lists) < 2 else [{"id": "dlv_v"}], "next_cursor": None})

    stub.on("GET", "/webhooks/endpoints/whep_01/deliveries/", by_event)
    stub.on("GET", "/webhooks/deliveries/dlv_v/", ok({"id": "dlv_v", "status": "failed", "attempts": [
        {"n": 1, "response_status": 503, "outcome": "http_error", "duration_ms": 30, "response_body_excerpt": "busy"}]}))
    assert run("test", "whep_01", "--event", "prompt.label.changed", "--wait", "30s") == 1
    assert lists[0] == {"event": "evt_test_3", "limit": "1"} and len(lists) == 2
    assert "503" in capsys.readouterr().out


def test_rotate_secret_follows_the_same_secret_rules(stub, capsys, tmp_path):
    stub.on("POST", "/webhooks/endpoints/whep_01/rotate-secret/", ok({
        "secret": SECRET, "id": "whk_2", "tail": SECRET[-4:], "previous": {"tail": "AAAA", "expires_at": "t"},
        "revoked_tails": []}))
    assert run("rotate-secret", "whep_01", "--overlap", "1h") == 2 and stub.seen == []
    target = tmp_path / "s"
    assert run("rotate-secret", "whep_01", "--overlap", "1h", "--secret-out", str(target)) == 0
    assert target.read_text().strip() == SECRET and stat.S_IMODE(os.stat(target).st_mode) == 0o600
    assert stub.calls("POST", "/webhooks/endpoints/whep_01/rotate-secret/")[0]["body"] == {"overlap_seconds": 3600}
    assert SECRET not in capsys.readouterr().out


def test_bulk_redeliver_counts_first_and_asks(stub, capsys):
    stub.on("POST", "/webhooks/deliveries/redeliver/", lambda req: ok({
        "count": 25, "queued": 0 if req["body"]["dry_run"] else 25, "expired": 0, "dry_run": req["body"]["dry_run"]}))
    assert run("redeliver", "--endpoint", "whep_01", "--status", "failed", "--since", "24h") == 2
    assert [c["body"]["dry_run"] for c in stub.calls("POST", "/webhooks/deliveries/redeliver/")] == [True]
    assert run("redeliver", "--endpoint", "whep_01", "--status", "failed", "--since", "24h", "--yes", "--json") == 0
    assert [c["body"]["dry_run"] for c in stub.calls("POST", "/webhooks/deliveries/redeliver/")] == [True, True, False]
    assert json.loads(capsys.readouterr().out)["queued"] == 25


def test_redeliver_several_ids_reports_each_one_queued_before_a_refusal(stub, capsys):
    stub.on("POST", "/webhooks/deliveries/dlv_a/redeliver/", ok({"delivery_id": "dlv_a", "attempt": 2}, 202))
    stub.on("POST", "/webhooks/deliveries/dlv_b/redeliver/", ok({"delivery_id": "dlv_b", "attempt": 4}, 202))
    stub.on("POST", "/webhooks/deliveries/dlv_x/redeliver/", refuse(409, "WEBHOOK_BODY_EXPIRED"))
    assert run("redeliver", "dlv_a", "dlv_b", "--json") == 0
    assert [r["delivery_id"] for r in json.loads(capsys.readouterr().out)["results"]] == ["dlv_a", "dlv_b"]
    assert run("redeliver", "dlv_a", "dlv_x", "dlv_b") == 3
    out, err = capsys.readouterr()
    assert out == "Queued dlv_a (attempt 2)\n" and "WEBHOOK_BODY_EXPIRED" in err  # dlv_b is not tried after a refusal
    assert len(stub.calls("POST", "/webhooks/deliveries/dlv_b/redeliver/")) == 1
    assert run("redeliver", "dlv_a", "--endpoint", "whep_01", "--status", "failed") == 2


def test_list_get_and_deliveries_json_shapes(stub, capsys):
    stub.on("GET", "/webhooks/endpoints/", ok({"results": [EP]}))
    stub.on("GET", "/webhooks/endpoints/whep_01/", ok(EP))
    stub.on("GET", "/webhooks/endpoints/whep_01/deliveries/", ok({"results": [], "next_cursor": None}))
    assert run("list", "--json") == 0
    assert json.loads(capsys.readouterr().out)["results"][0]["id"] == "whep_01"
    assert run("get", "whep_01", "--json") == 0
    assert json.loads(capsys.readouterr().out)["subscriptions"][0]["event_type"] == "prompt.label.changed"
    assert run("deliveries", "whep_01", "--seq", "40-45", "--status", "failed", "--json") == 0
    assert json.loads(capsys.readouterr().out) == {"results": [], "next_cursor": None}
    q = stub.calls("GET", "/webhooks/endpoints/whep_01/deliveries/")[0]["query"]
    assert q == {"seq_from": "40", "seq_to": "45", "status": "failed", "limit": "20"}
    assert run("ls") == 0 and "hooks.acme.ai" in capsys.readouterr().out


def _vector_files(tmp_path, case, *, tamper=False):
    body = base64.b64decode(case["body_bytes_b64"])
    if tamper:
        body = body[:10] + bytes([body[10] ^ 1]) + body[11:]
    (tmp_path / "body").write_bytes(body)
    (tmp_path / "headers").write_text("POST /hook HTTP/1.1\n" + "".join(f"{k}: {v}\n" for k, v in case["headers"].items()))
    (tmp_path / "secret").write_text(case["secret"] + "\n")
    return ["--secret-file", str(tmp_path / "secret"), "--headers-file", str(tmp_path / "headers"),
            "--body-file", str(tmp_path / "body"), "--now", str(case["now"])]


def test_verify_checks_the_design_vectors_offline(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")  # never contacted
    cases = json.loads((CONF / "signing.json").read_text())["verify"]
    for case in cases:
        args = _vector_files(tmp_path, case)
        code = run("verify", *args, "--json")
        out = json.loads(capsys.readouterr().out)
        assert (code == 0) is (case["expected"] == "ok"), case["id"]
        assert out["verified"] is (case["expected"] == "ok")
        if case["expected"] != "ok":
            assert out["reason"] == case["expected"], case["id"]
    a_ok = next(c for c in cases if c["id"] == "a-ok")
    assert run("verify", *_vector_files(tmp_path, a_ok, tamper=True)) == 1
    assert "no_matching_signature" in capsys.readouterr().err


def test_verify_tolerance_s_widens_and_narrows_the_timestamp_window(tmp_path, capsys):
    a_ok = next(c for c in json.loads((CONF / "signing.json").read_text())["verify"] if c["id"] == "a-ok")
    args = _vector_files(tmp_path, a_ok)[:-1]  # drop the vector's own --now value
    t = int(a_ok["headers"]["webhook-timestamp"])
    assert run("verify", *args, str(t + 301), "--json") == 1
    assert json.loads(capsys.readouterr().out)["reason"] == "timestamp_too_old"
    assert run("verify", *args, str(t + 301), "--tolerance-s", "400", "--json") == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True
    assert run("verify", *args, str(t - 60), "--tolerance-s", "30", "--json") == 1
    assert json.loads(capsys.readouterr().out)["reason"] == "timestamp_too_new"


def test_verify_takes_the_secret_from_the_environment_never_argv(tmp_path, capsys, monkeypatch):
    case = json.loads((CONF / "signing.json").read_text())["verify"][0]
    args = _vector_files(tmp_path, case)
    args = args[2:]  # drop --secret-file
    monkeypatch.delenv("FI_WEBHOOK_SECRET", raising=False)
    assert run("verify", *args) == 2
    monkeypatch.setenv("FI_WEBHOOK_SECRET", case["secret"])
    assert run("verify", *args) == 0
    with pytest.raises(SystemExit):
        cli_main.build_parser(warn=lambda m: None).parse_args(["webhooks", "verify", "--secret", "x"])


@pytest.mark.skipif(sys.platform == "win32", reason="pty")
def test_create_prints_the_secret_on_a_terminal(stub, tmp_path):
    """The terminal branch of the secret rules, in a real pseudo-terminal: the secret goes to stdout with a warning on stderr."""
    import pty
    import subprocess

    stub.on("POST", "/webhooks/endpoints/", ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    master, slave = pty.openpty()
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
    code = ("import fi._cli.registry as r, fi.webhooks._cli as m\n"
            "class E:\n name='webhooks'\n def load(self): return m\n"
            "r.entry_points = lambda: [E()]\n"
            "import fi._cli.main as c; raise SystemExit(c.main(['webhooks','create','--url',"
            "'https://hooks.acme.ai/fi','--event','prompt.*']))")
    proc = subprocess.Popen([sys.executable, "-c", code], stdout=slave, stderr=subprocess.PIPE, env=env)
    os.close(slave)  # the child holds its own copy; reading the master sees EOF / EIO once it exits
    out = b""
    while True:
        try:
            chunk = os.read(master, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
    stderr = proc.stderr.read()
    proc.wait(timeout=60)
    os.close(master)
    assert proc.returncode == 0, stderr
    assert SECRET in out.decode() and b"only time" in stderr


def test_update_maps_every_flag_to_the_patch_body(stub, capsys, tmp_path, monkeypatch):
    stub.on("PATCH", "/webhooks/endpoints/whep_01/", ok(EP))
    hf = tmp_path / "h.txt"
    hf.write_text("X-File: ${{ env.SECRET_KEY }}\n")
    monkeypatch.setenv("WH4_UPD", "env-value")
    assert run("update", "whep_01", "--url", "https://h2.acme.ai/x", "--event", "prompt.label.changed", "--event",
               "deployment.run.failed", "--name", "n2", "--description", "d2", "--prompt", "p-1", "--exclude-prompt",
               "p-2", "--label", "Staging", "--action", "removed", "--deployment", "dep-1", "--environment", "prod",
               "--trigger", "cron", "--status", "interrupted", "--header", "X-A: 1", "--header-file", str(hf),
               "--header-env", "X-B=WH4_UPD", "--payload", "full", "--names", "--no-run-targeting", "--timeout-s",
               "7.5", "--rate-limit", "3", "--max-in-flight", "2", "--max-age", "12h", "--json") == 0
    assert json.loads(capsys.readouterr().out)["id"] == "whep_01"
    (patch,) = stub.calls("PATCH", "/webhooks/endpoints/whep_01/")
    assert patch["body"] == {
        "url": "https://h2.acme.ai/x", "name": "n2", "description": "d2",
        "subscriptions": [
            {"event_type": "prompt.label.changed", "filters": {"prompt_ids": ["p-1"], "exclude_prompt_ids": ["p-2"],
                                                               "label_names": ["Staging"], "actions": ["removed"]}},
            {"event_type": "deployment.run.failed", "filters": {"deployment_ids": ["dep-1"], "environments": ["prod"],
                                                                "trigger_kinds": ["cron"], "statuses": ["interrupted"]}},
        ],
        "headers": {"X-A": "1", "X-File": "${{ env.SECRET_KEY }}", "X-B": "env-value"},
        "payload_mode": "full", "include_people_names": True, "accepts_run_targeting": False, "timeout_ms": 7500,
        "rate_limit_per_s": 3, "max_in_flight": 2, "max_age_s": 43200,
    }


def test_update_names_switches_clear_headers_and_refusals(stub, capsys):
    stub.on("PATCH", "/webhooks/endpoints/whep_01/", ok(EP))
    assert run("update", "whep_01", "--no-names", "--accept-run-targeting", "--clear-headers") == 0
    assert "Updated whep_01" in capsys.readouterr().err
    assert run("update", "whep_01", "--names") == 0
    bodies = [c["body"] for c in stub.calls("PATCH", "/webhooks/endpoints/whep_01/")]
    assert bodies == [{"include_people_names": False, "accepts_run_targeting": True, "headers": None},
                      {"include_people_names": True}]
    n = len(stub.seen)
    assert run("update", "whep_01", "--clear-headers", "--header", "X-A: 1") == 2
    assert run("update", "whep_01", "--label", "Production") == 2  # filters replace subscriptions: need --event
    assert run("update", "whep_01") == 2  # nothing to change
    assert len(stub.seen) == n
    err = capsys.readouterr().err
    assert "--clear-headers or header flags" in err and "filter flags need --event" in err and "nothing to update" in err


@pytest.mark.parametrize("argv", [
    ("deliveries", "whep_01", "--since", "banana"),
    ("deliveries", "whep_01", "--until", "x1"),
    ("deliveries", "whep_01", "--seq", "5-2"),
    ("rotate-secret", "whep_01", "--overlap", "banana", "--show-secret"),
    ("rotate-secret", "whep_01", "--overlap", "8d", "--show-secret"),
    ("create", "--url", "https://h.acme.ai/x", "--event", "prompt.*", "--max-age", "1y", "--show-secret"),
    ("create", "--url", "https://h.acme.ai/x", "--event", "prompt.*", "--timeout-s", "inf", "--show-secret"),
    ("update", "whep_01", "--timeout-s", "nan"),
    ("test", "whep_01", "--wait", "soon"),
    ("events", "--list", "--since", "yesterday"),
    ("redeliver", "--endpoint", "whep_01", "--status", "failed", "--since", "zz", "--dry-run"),
])
def test_a_malformed_value_is_a_usage_error_before_any_request(stub, capsys, argv):
    assert run(*argv) == 2
    err = capsys.readouterr().err
    assert stub.seen == [] and "error" in err and "Traceback" not in err


def test_overlap_zero_and_bare_seconds_and_iso_times_are_accepted(stub, capsys):
    stub.on("POST", "/webhooks/endpoints/whep_01/rotate-secret/",
            ok({"secret": SECRET, "previous": None, "revoked_tails": ["AAAA"]}))
    stub.on("GET", "/webhooks/endpoints/whep_01/deliveries/", ok({"results": [], "next_cursor": None}))
    assert run("rotate-secret", "whep_01", "--overlap", "0", "--show-secret") == 0
    assert stub.calls("POST", "/webhooks/endpoints/whep_01/rotate-secret/")[0]["body"] == {"overlap_seconds": 0}
    assert "…AAAA stopped working now" in capsys.readouterr().err
    assert run("deliveries", "whep_01", "--since", "2026-10-23T09:00:00Z", "--until", "90", "--json") == 0
    q = stub.calls("GET", "/webhooks/endpoints/whep_01/deliveries/")[0]["query"]
    assert q["since"] == "2026-10-23T09:00:00Z" and q["until"].endswith("Z") and len(q["until"]) == 20


def test_events_list_pages_with_cursor_and_until(stub, capsys):
    ev = {"id": "evt_1", "type": "prompt.label.changed", "timestamp": "2026-10-23T00:00:00Z", "subject": "prompt:p1",
          "delivery_count": 1}
    stub.on("GET", "/webhooks/events/", ok({"results": [ev], "next_cursor": "evt_0"}))
    assert run("events", "--list", "--type", "prompt.label.changed", "--since", "2026-10-22T00:00:00Z", "--until",
               "1h", "--limit", "1", "--cursor", "evt_9") == 0
    out, err = capsys.readouterr()
    assert "evt_1" in out and "more: --cursor evt_0" in err
    q = stub.calls("GET", "/webhooks/events/")[0]["query"]
    assert q["type"] == "prompt.label.changed" and q["since"] == "2026-10-22T00:00:00Z" and q["cursor"] == "evt_9"
    assert q["limit"] == "1" and q["until"].endswith("Z")
    n = len(stub.seen)
    assert run("events", "--cursor", "evt_9") == 2 and "goes with --list" in capsys.readouterr().err
    assert len(stub.seen) == n


# ---- --secret-out keeps the current secret until the new one has arrived (regression coverage) --------------------------------

OLD_SECRET = "whsec_QEFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaW1xdXl8="
_SECRET_PATHS = {"create": "/webhooks/endpoints/", "rotate-secret": "/webhooks/endpoints/whep_01/rotate-secret/"}


def _secret_argv(command, target):
    head = ["create", "--url", "https://hooks.acme.ai/fi", "--event", "prompt.*"] if command == "create" else \
        ["rotate-secret", "whep_01", "--overlap", "24h"]
    return [*head, "--secret-out", str(target)]


def _a_receivers_secret_file(tmp_path):
    target = tmp_path / "hook-secret"
    target.write_text(OLD_SECRET + "\n")
    os.chmod(target, 0o600)
    return target


@pytest.mark.parametrize("command", ["create", "rotate-secret"])
@pytest.mark.parametrize("failure", ["refused_403", "not_found_404", "connection_dropped", "ctrl_c"])
def test_a_failed_request_leaves_the_existing_secret_file_as_it_was(stub, capsys, tmp_path, monkeypatch, command,
                                                                     failure):
    """The README's own flow: ``create --secret-out ./hook-secret``, later ``rotate-secret ... --secret-out
    ./hook-secret``. Before M1's fix a refused rotate left the file empty: the receiver had no secret and the user no
    copy. Now the file is replaced only after the secret arrives, and no temporary file is left behind."""
    target = _a_receivers_secret_file(tmp_path)
    path = _SECRET_PATHS[command]
    if failure == "refused_403":
        stub.on("POST", path, refuse(403, "WEBHOOK_FORBIDDEN"))
    elif failure == "connection_dropped":  # the request was sent; the connection closed before any answer
        stub.on("POST", path, HANGUP)
    elif failure == "ctrl_c":
        from fi.webhooks import _client

        def interrupted(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(_client._Endpoints, "create" if command == "create" else "rotate_secret", interrupted)
    code = run(*_secret_argv(command, target))
    out, err = capsys.readouterr()
    assert code == (4 if failure == "ctrl_c" else 3), (code, err)
    assert target.read_text() == OLD_SECRET + "\n"
    assert stat.S_IMODE(os.stat(target).st_mode) == 0o600
    assert sorted(p.name for p in tmp_path.iterdir()) == ["hook-secret"]
    assert OLD_SECRET not in out + err
    if failure != "ctrl_c":
        assert len(stub.calls("POST", path)) == 1


@pytest.mark.parametrize("command", ["create", "rotate-secret"])
def test_a_successful_request_replaces_the_secret_file_and_leaves_no_temporary_file(stub, capsys, tmp_path, command):
    answer = {"endpoint": EP, "secret": SECRET, "warnings": []} if command == "create" else \
        {"secret": SECRET, "id": "whk_2", "tail": SECRET[-4:], "previous": {"tail": "XXXX", "expires_at": "t"},
         "revoked_tails": []}
    stub.on("POST", _SECRET_PATHS[command], ok(answer, 201 if command == "create" else 200))
    target = _a_receivers_secret_file(tmp_path)
    os.chmod(target, 0o644)
    assert run(*_secret_argv(command, target)) == 0
    out, err = capsys.readouterr()
    assert target.read_text() == SECRET + "\n" and stat.S_IMODE(os.stat(target).st_mode) == 0o600
    assert sorted(p.name for p in tmp_path.iterdir()) == ["hook-secret"]
    assert SECRET not in out + err and f"…{SECRET[-4:]}, mode 0600" in out


def test_secret_out_replaces_a_symlink_and_never_writes_through_it(stub, capsys, tmp_path):
    stub.on("POST", _SECRET_PATHS["create"], ok({"endpoint": EP, "secret": SECRET, "warnings": []}, 201))
    real = tmp_path / "elsewhere"
    real.write_text("not yours\n")
    link = tmp_path / "hook-secret"
    link.symlink_to(real)
    assert run(*_secret_argv("create", link)) == 0
    assert real.read_text() == "not yours\n"
    assert not link.is_symlink() and link.read_text() == SECRET + "\n"


def test_secret_out_naming_a_directory_stops_before_any_request(stub, capsys, tmp_path):
    assert run(*_secret_argv("create", tmp_path)) == 2
    assert stub.seen == [] and "is a directory" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_a_secret_that_cannot_be_moved_into_place_is_kept_and_its_file_named(stub, capsys, tmp_path, monkeypatch):
    stub.on("POST", _SECRET_PATHS["rotate-secret"], ok({"secret": SECRET, "previous": None, "revoked_tails": []}))
    target = _a_receivers_secret_file(tmp_path)

    def no_rename(src, dst):
        raise PermissionError(1, "Operation not permitted")

    monkeypatch.setattr("fi.webhooks._cli_io.os.replace", no_rename)
    assert run(*_secret_argv("rotate-secret", target)) == 3
    err = capsys.readouterr().err
    assert target.read_text() == OLD_SECRET + "\n"
    (kept,) = [p for p in tmp_path.iterdir() if p.name != "hook-secret"]
    assert kept.read_text() == SECRET + "\n" and stat.S_IMODE(os.stat(kept).st_mode) == 0o600
    assert str(kept) in err and "Operation not permitted" in err and SECRET not in err


# ---- the server's secret is checked before it is written or printed (regression coverage) ------------------------------------


@pytest.mark.parametrize("command", ["create", "rotate-secret"])
@pytest.mark.parametrize("to", ["file", "show", "json"])
@pytest.mark.parametrize("bad", [f"whsec_{chr(27)}[31mAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", "whsec_AAAA", "sk_nope", None])
def test_a_malformed_secret_from_the_server_is_neither_written_nor_printed(stub, capsys, tmp_path, command, to, bad):
    answer = {"endpoint": EP, "secret": bad, "warnings": []} if command == "create" else \
        {"secret": bad, "previous": None, "revoked_tails": []}
    stub.on("POST", _SECRET_PATHS[command], ok(answer, 201 if command == "create" else 200))
    target = _a_receivers_secret_file(tmp_path)
    argv = _secret_argv(command, target)
    if to != "file":
        argv = argv[:-2] + ["--show-secret"] + (["--json"] if to == "json" else [])
    assert run(*argv) == 3
    out, err = capsys.readouterr()
    assert chr(27) not in out + err and "AAAA" not in out + err and "sk_nope" not in out + err
    message = json.loads(out)["error"]["message"] if to == "json" else err
    assert "not whsec_ plus padded base64" in message and "rotate-secret whep_01" in message
    assert target.read_text() == OLD_SECRET + "\n" and sorted(p.name for p in tmp_path.iterdir()) == ["hook-secret"]


# ---- header inputs never echo a header line (regression coverage) ------------------------------------------------------------


def test_a_malformed_header_file_line_is_refused_by_its_number_only(stub, capsys, tmp_path):
    hf = tmp_path / "h.txt"
    hf.write_text("X-Ok: 1\n# note\nAuthorization Bearer sk-live-SUPERSECRETVALUE\n")
    base = ["create", "--url", "https://h.acme.ai/x", "--event", "prompt.*", "--header-file", str(hf), "--show-secret"]
    assert run(*base) == 2
    err = capsys.readouterr().err
    assert "--header-file line 3" in err
    assert "SUPERSECRET" not in err and "sk-live" not in err and "Bearer" not in err and "Authorization" not in err
    assert run(*base, "--json") == 2
    out = capsys.readouterr().out
    assert "line 3" in json.loads(out)["error"]["message"] and "sk-live" not in out
    assert stub.seen == []


def test_malformed_header_and_header_env_flags_are_not_echoed_either(stub, capsys):
    base = ["create", "--url", "https://h.acme.ai/x", "--event", "prompt.*", "--show-secret"]
    assert run(*base, "--header", "X-A: 1", "--header", "Authorization Bearer sk-live-ARGVSECRET") == 2
    err = capsys.readouterr().err
    assert "--header #2" in err and "ARGVSECRET" not in err and "Bearer" not in err
    assert run(*base, "--header-env", "Authorization=Bearer sk-live-ENVSECRET") == 2
    err = capsys.readouterr().err
    assert "--header-env #1" in err and "ENVSECRET" not in err and "Bearer" not in err
    assert run(*base, "--header-env", "sk-live-NOEQUALS") == 2
    assert "NOEQUALS" not in capsys.readouterr().err
    assert stub.seen == []


# ---- redeliver refuses bulk flags with ids; help and confirmations (regression coverage, S8) ----------------------------------


@pytest.mark.parametrize("flag", [("--status", "failed"), ("--event", "prompt.label.changed"), ("--since", "24h"),
                                  ("--until", "1h"), ("--dry-run",), ("--yes",)])
def test_redeliver_with_ids_refuses_the_bulk_flags_instead_of_ignoring_them(stub, capsys, flag):
    stub.on("POST", "/webhooks/deliveries/dlv_1/redeliver/", ok({"delivery_id": "dlv_1", "attempt": 2}, 202))
    assert run("redeliver", "dlv_1", *flag) == 2
    err = capsys.readouterr().err
    assert f"{flag[0]} goes with --endpoint" in err and "Nothing was queued" in err
    assert stub.seen == []


def test_subcommand_help_names_the_command_and_its_id(capsys):
    assert run("create", "--help") == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: futureagi-py webhooks create ") and "COMMAND ..." not in out
    for argv, text in ((("get", "--help"), "the endpoint's id (whep_"), (("delivery", "--help"), "the delivery's id"),
                       (("redeliver", "--help"), "delivery ids to send again")):
        assert run(*argv) == 0
        out = capsys.readouterr().out
        assert out.startswith(f"usage: futureagi-py webhooks {argv[0]} ") and text in out, out


class _Answer:
    """A stdin that is a terminal and answers the confirmation question with ``text``."""

    def __init__(self, text):
        self.text = text

    def isatty(self):
        return True

    def readline(self):
        return self.text + "\n"


def test_answering_no_to_a_confirmation_exits_4_and_does_nothing(stub, capsys, monkeypatch):
    """Declining is the user stopping the command, as Ctrl-C at the same question is (exit 4), not a usage error."""
    stub.on("GET", "/webhooks/endpoints/whep_01/", ok(EP))
    stub.on("DELETE", "/webhooks/endpoints/whep_01/", ok({"deleted": True, "id": "whep_01", "cancelled_deliveries": 0}))
    stub.on("POST", "/webhooks/deliveries/redeliver/", lambda req: ok({
        "count": 3, "queued": 0 if req["body"]["dry_run"] else 3, "expired": 0, "dry_run": req["body"]["dry_run"]}))
    monkeypatch.setattr("sys.stdin", _Answer("n"))
    assert run("delete", "whep_01") == 4
    assert "Not deleted." in capsys.readouterr().err and stub.calls("DELETE", "/webhooks/endpoints/whep_01/") == []
    assert run("redeliver", "--endpoint", "whep_01", "--status", "failed") == 4
    assert "Nothing queued." in capsys.readouterr().err
    assert [c["body"]["dry_run"] for c in stub.calls("POST", "/webhooks/deliveries/redeliver/")] == [True]
    monkeypatch.setattr("sys.stdin", _Answer("y"))
    assert run("delete", "whep_01") == 0 and len(stub.calls("DELETE", "/webhooks/endpoints/whep_01/")) == 1
