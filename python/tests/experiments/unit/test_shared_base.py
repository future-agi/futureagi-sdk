"""fi.experiments on the shared base: its errors subclass fi.errors, and its CLI group registers the
hooks the core no longer hard-codes (the shared client plugin contract)."""

import fi.errors as fe
from fi.experiments import errors as xe
from tests.experiments.unit.cli_helpers import cli


def test_every_experiments_error_is_in_the_public_tree():
    for name in xe.__all__:
        cls = getattr(xe, name)
        if name == "RunInterrupted":  # a KeyboardInterrupt by design: Ctrl-C is never swallowed
            assert issubclass(cls, KeyboardInterrupt)
            continue
        assert issubclass(cls, fe.FutureAGIError), name


def test_matching_classes_subclass_their_fi_errors_twin():
    assert issubclass(xe.ServerUnreachableError, fe.TransportError)
    assert issubclass(xe.MissingExtraError, fe.MissingExtraError)
    assert issubclass(xe.HostedEvalNeedsServerError, fe.AuthError)
    assert issubclass(xe.CredentialsMissingError, fe.AuthError)

    err = xe.MissingExtraError("langgraph", "traceai_langchain")
    assert (err.extra, err.module, err.install_hint) == ("langgraph", "traceai_langchain",
                                                         'pip install "futureagi[langgraph]"')
    assert str(err) == 'traceai_langchain is not installed. Run: pip install "futureagi[langgraph]"'
    assert err.get_error_code() == "MISSING_EXTRA" and err.exit_code == 3

    unreachable = xe.ServerUnreachableError("http://srv.test", "refused")
    assert (unreachable.base_url, unreachable.reason) == ("http://srv.test", "refused")
    assert unreachable.get_error_code() == "SERVER_UNREACHABLE"
    assert "local evaluators only" in str(unreachable)


def test_run_is_listed_under_evaluate_and_doctor_under_setup():
    code, out, _ = cli("--help")
    assert code == 0
    evaluate = out.split("Evaluate:\n", 1)[1].split("\n\n", 1)[0]
    setup = out.split("Setup:\n", 1)[1].split("\n\n", 1)[0]
    assert "run" in {line.split()[0] for line in evaluate.splitlines()}
    assert "doctor" in {line.split()[0] for line in setup.splitlines()}


def test_the_group_registers_its_hooks_and_doctor_arguments():
    from fi._cli import registry
    from fi._cli.main import build_parser
    from fi.experiments._cli import commands

    parser = build_parser()
    assert commands._pre_parse in registry._PRE_PARSE
    assert commands._interrupt_message in registry._ON_INTERRUPT
    assert commands._flush_task_threads in registry._ON_EXIT
    args = parser.parse_args(["doctor", "agent.py:task", "--dataset", "rows.jsonl", "--judge-model", "m"])
    assert (args.target, args.dataset, args.judge_model) == ("agent.py:task", "rows.jsonl", "m")
    assert parser.parse_args(["run", "agent.py:task"]).install_hint == commands.INSTALL_HINT


def test_run_dash_dash_is_refused_by_the_pre_parse_hook():
    code, _, err = cli("run", "--", "python", "app.py")
    assert code == 2 and "TARGET" in err and "Traceback" not in err


def test_interrupt_hook_answers_only_for_a_run():
    from fi.experiments._cli.commands import _interrupt_message

    assert _interrupt_message(KeyboardInterrupt(), ["run", "a.py:t"]) is None
    exc = xe.RunInterrupted("R1", 1, 4)
    message = _interrupt_message(exc, ["run", "a.py:t", "--dataset", "rows.jsonl"])
    assert message == (
        "Interrupted. The journal is kept. Resume with:\n"
        "  futureagi-py run a.py:t --dataset rows.jsonl --resume R1"
    )


# ---- L-SHARED review fixes (S5, S8, S3) -----------------------------------------------------------


def test_unreachable_words_a_timeout_and_a_reset_apart_from_a_refusal():
    import httpx

    req = httpx.Request("GET", "http://srv.test:8000/x")
    refused = xe.server_unreachable(httpx.ConnectError("refused", request=req))
    assert refused.kind == "connect" and str(refused).startswith("cannot reach http://srv.test:8000 (refused)")
    slow = xe.server_unreachable(httpx.ReadTimeout("read timed out", request=req))
    assert slow.kind == "timeout" and "did not answer in time" in str(slow) and "cannot reach" not in str(slow)
    reset = xe.server_unreachable(httpx.ReadError("reset", request=req))
    assert reset.kind == "connection" and "broke before a response" in str(reset)
    for err in (refused, slow, reset):
        assert isinstance(err, fe.TransportError) and "local evaluators only" in str(err)


def test_run_adds_its_no_upload_hint_to_a_missing_keys_error(monkeypatch):
    """S8: the shared message names no CLI flag; `futureagi-py run` adds --no-upload itself."""
    from argparse import Namespace

    from fi._credentials import CredentialsMissingError, MissingAuthError
    from fi.experiments._cli import commands, run as run_mod

    def no_keys(args):
        raise MissingAuthError(None, None, base_url="http://x.test")

    monkeypatch.setattr(run_mod, "run_command", no_keys)
    try:
        commands._run_command(Namespace())
    except CredentialsMissingError as exc:
        assert "Or add --no-upload to run locally without a server." in str(exc)
        assert isinstance(exc.__cause__, MissingAuthError) and exc.missing == ("FI_API_KEY", "FI_SECRET_KEY")
    else:
        raise AssertionError("no error")
    assert "--no-upload" not in str(CredentialsMissingError("http://x.test", ("FI_API_KEY",)))


def test_doctor_json_carries_the_experiments_section(tmp_path):
    import json

    code, out, _ = cli("doctor", "--json")
    assert code == 0
    doc = json.loads(out)
    assert "experiments" in doc["sections"] and doc["keys"]["source"] in ("none", "env", "argument", "login")
